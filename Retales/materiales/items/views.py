import hmac
import json
from decimal import Decimal
from functools import wraps

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
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


@csrf_exempt
@service_token_required
@require_http_methods(['GET', 'POST'])
def items(request):
    if request.method == 'GET':
        return JsonResponse({'items': [serialize(i) for i in Item.objects.prefetch_related('composicion')[:100]]})

    try:
        payload = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    composicion = payload.get('composition') or []
    if not isinstance(composicion, list):
        return JsonResponse({'error': 'composition debe ser una lista'}, status=400)

    item = Item(
        titulo=str(payload.get('title', '')).strip(),
        descripcion=str(payload.get('description', '')).strip(),
        creado_por=str(payload.get('created_by', '')).strip(),
        tam_lana=payload.get('yarn_weight') or Item.TamLana.SPORT,
        tam_aguja_mm=payload.get('needle_mm'),
        tam_ganchillo_mm=payload.get('hook_mm'),
        marca=str(payload.get('brand', '')).strip(),
    )
    try:
        with transaction.atomic():
            item.full_clean()
            item.save()
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

    item.refresh_from_db() 
    return JsonResponse(serialize(item), status=201)