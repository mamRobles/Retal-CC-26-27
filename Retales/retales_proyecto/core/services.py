'''Cliente HTTP del microservicio.

Toda la comunicación con el otro servicio vive aquí, no en las vistas:
si mañana cambia la API del microservicio, solo se toca este archivo.
'''
import requests
from django.conf import settings
from django.utils.dateparse import parse_datetime


class MicroserviceError(Exception):
    '''El microservicio no respondió o devolvió un error.

    Si la API rechazó los datos (400), `errores` trae su detalle como
    {campo: [mensajes]}; los nombres de campo son los del modelo de la API.
    '''

    def __init__(self, mensaje, errores=None):
        super().__init__(mensaje)
        self.errores = errores or {}

class MaterialNoEncontrado(MicroserviceError):
    '''La API respondió 404: ese material no existe.'''


def _errores_400(response):
    '''Extrae {'error': ...} de una respuesta 400 de la API como {campo: [mensajes]}.'''
    try:
        detalle = response.json().get('error')
    except (ValueError, AttributeError):
        return {}
    if isinstance(detalle, dict):
        return {campo: m if isinstance(m, list) else [m] for campo, m in detalle.items()}
    return {'__all__': [str(detalle)]} if detalle else {}


def _request(method, path, **kwargs):
    url = f'{settings.MICROSERVICE_URL}{path}'
    headers = {'X-Service-Token': settings.SERVICE_TOKEN}
    try:
        response = requests.request(
            method, url, headers=headers, timeout=settings.MICROSERVICE_TIMEOUT, **kwargs
        )
        response.raise_for_status()
        if response.status_code == 204: # sin cuerpo es DELETE
            return None
        return response.json()
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            raise MaterialNoEncontrado('Ese material no existe.') from exc
        if exc.response is not None and exc.response.status_code == 400:
            raise MicroserviceError(
                'El servicio de materiales rechazó los datos.', _errores_400(exc.response)
            ) from exc
        raise MicroserviceError(f'Error del servicio de materiales ({exc.__class__.__name__}).') from exc
    except requests.RequestException as exc:
        raise MicroserviceError(f'No se pudo contactar con el servicio de materiales ({exc.__class__.__name__}).') from exc


def list_items():
    params = {'created_by': created_by} if created_by else None
    data = _request('GET', '/api/items/', params=params)
    items = data.get('items', [])
    for item in items:
        item['created_at'] = parse_datetime(item['created_at'])
    return items

def get_choices():
    data = _request(
        'GET',
        '/api/choices/'
    )
    return {
        campo: [(o['value'], o['label']) for o in opciones]
        for campo, opciones in data.items()
    }
def create_item(title, description, created_by,**extra):
    return _request(
        'POST',
        '/api/items/',
        json={'title': title, 'description': description, 'created_by': created_by, **extra},   
    )
def get_item(item_id):
    item = _request('GET', f'/api/items/{item_id}/')
    item['created_at'] = parse_datetime(item['created_at'])
    return item


def delete_item(item_id):
    _request('DELETE', f'/api/items/{item_id}/')

def update_item(item_id, **campos):
    return _request('PUT', f'/api/items/{item_id}/', json=campos)

