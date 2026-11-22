import hmac
import json
from decimal import Decimal
from functools import wraps

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Composicion, Item


def service_token_required(view):
    '''Exige la cabecera X-Service-Token (autenticación entre servicios).'''

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        sent = request.headers.get('X-Service-Token', '').encode()
        expected = settings.SERVICE_TOKEN.encode()
        # compare_digest compara en tiempo constante (evita ataques de temporización)
        if not expected or not hmac.compare_digest(sent, expected):
            return JsonResponse({'error': 'unauthorized'}, status=401)
        return view(request, *args, **kwargs)

    return wrapper


def serialize(item):
    # El modelo usa nombres en español, pero el contrato JSON con Retales
    # (core/services.py) sigue en inglés: solo se traduce aquí.
    return {
        'id': item.id,
        'title': item.titulo,
        'description': item.descripcion,
        'created_by': item.creado_por,
        'created_at': item.creado_a.isoformat(),
        'yarn_weight': item.tam_lana,
        'yarn_weight_display': item.get_tam_lana_display(),
        'needle_mm': str(item.tam_aguja_mm) if item.tam_aguja_mm is not None else None,
        'hook_mm': str(item.tam_ganchillo_mm) if item.tam_ganchillo_mm is not None else None,
        'brand': item.marca,
        'composition': [
            {'fiber': c.fibra, 'fiber_display': c.get_fibra_display(), 'percent': str(c.porcentaje)}
            for c in item.composicion.all()
        ],
    }


def health(request):
    return JsonResponse({'status': 'ok'})


def _opciones(choices):
    return [{'value': value, 'label': label} for value, label in choices]


@service_token_required
@require_http_methods(['GET'])
def choices(request):
    '''Opciones válidas de los campos con choices. Los modelos de este servicio son
    la única fuente de verdad: Retales las pide aquí en vez de copiarlas.'''
    return JsonResponse({
        'yarn_weight': _opciones(Item.TamLana.choices),
        'fiber': _opciones(Composicion.Fibra.choices),
    })

def _leer_payload(request):
    try:
        payload = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return None, None, JsonResponse({'error': 'JSON inválido'}, status=400)
    
    composicion =  payload.get('composition') or []
    if not isinstance(composicion, list):
        return None, None, JsonResponse({'error': 'Composition debe ser una lista'}, status=400)
    
    return payload, composicion, None

def _guardar(item, payload, composicion):
    item.titulo = str(payload.get('title', '')).strip()
    item.descripcion = str(payload.get('description', '')).strip()
    item.tam_lana = payload.get('yarn_weight') or Item.TamLana.SPORT
    item.tam_aguja_mm = payload.get('needle_mm')
    item.tam_ganchillo_mm = payload.get('hook_mm')
    item.marca = str(payload.get('brand', '')).strip()

    try:
        with transaction.atomic():
            item.full_clean()
            item.save()
            item.composicion.all().delete()  # al crear no hay nada; al editar se reemplaza
            total = Decimal(0)
            for c in composicion:
                fibra = Composicion(item=item, fibra=c.get('fiber'), porcentaje=c.get('percent'))
                fibra.full_clean()
                fibra.save()
                total += fibra.porcentaje
            if total > 100:
                raise ValidationError({'composition': 'Los porcentajes suman más de 100'})
    except (ValidationError, AttributeError) as exc:
        detalle = exc.message_dict if isinstance(exc, ValidationError) else 'formato no válido'
        return JsonResponse({'error': detalle}, status=400)
    return None
    
@csrf_exempt
@service_token_required
@require_http_methods(['GET', 'POST'])
def items(request):
    if request.method == 'GET':
        queryset = Item.objects.prefetch_related('composicion')
        created_by = request.GET.get('created_by')
        if created_by:  # ?created_by=ana -> solo los materiales de ana
            queryset = queryset.filter(creado_por=created_by)
        return JsonResponse({'items': [serialize(i) for i in queryset[:100]]})
        
    payload, composicion, error = _leer_payload(request)
    if error:
        return error

    item = Item(creado_por=str(payload.get('created_by', '')).strip())
    error = _guardar(item, payload, composicion)
    if error:
        return error

    item.refresh_from_db()
    return JsonResponse(serialize(item), status=201)


@csrf_exempt
@service_token_required
@require_http_methods(['GET', 'PUT', 'DELETE'])
def item_detail(request, item_id):
    try:
        item = Item.objects.prefetch_related('composicion').get(pk=item_id)
    except Item.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)

    if request.method == 'DELETE':
        item.delete()
        return HttpResponse(status=204)

    if request.method == 'PUT':
        payload, composicion, error = _leer_payload(request)
        if error:
            return error
        error = _guardar(item, payload, composicion)
        if error:
            return error
        item.refresh_from_db()

    return JsonResponse(serialize(item))