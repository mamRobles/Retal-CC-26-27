import hmac
import json
from functools import wraps

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Item


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
    }


def health(request):
    return JsonResponse({'status': 'ok'})


# CSRF protege formularios de navegador con cookies; esta API la consume otro
# servidor con token, así que no aplica.
@csrf_exempt
@service_token_required
@require_http_methods(['GET', 'POST'])
def items(request):
    if request.method == 'GET':
        return JsonResponse({'items': [serialize(i) for i in Item.objects.all()[:100]]})

    try:
        payload = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    title = str(payload.get('title', '')).strip()
    created_by = str(payload.get('created_by', '')).strip()
    if not title or len(title) > 200:
        return JsonResponse({'error': 'title es obligatorio (máx. 200 caracteres)'}, status=400)
    if not created_by or len(created_by) > 150:
        return JsonResponse({'error': 'created_by es obligatorio (máx. 150 caracteres)'}, status=400)

    item = Item.objects.create(
        titulo=title,
        descripcion=str(payload.get('description', '')).strip(),
        creado_por=created_by,
    )
    return JsonResponse(serialize(item), status=201)
