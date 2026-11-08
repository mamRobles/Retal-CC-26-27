'''Cliente HTTP del microservicio.

Toda la comunicación con el otro servicio vive aquí, no en las vistas:
si mañana cambia la API del microservicio, solo se toca este archivo.
'''
import requests
from django.conf import settings
from django.utils.dateparse import parse_datetime


class MicroserviceError(Exception):
    '''El microservicio no respondió o devolvió un error.'''


def _request(method, path, **kwargs):
    url = f'{settings.MICROSERVICE_URL}{path}'
    headers = {'X-Service-Token': settings.SERVICE_TOKEN}
    try:
        response = requests.request(
            method, url, headers=headers, timeout=settings.MICROSERVICE_TIMEOUT, **kwargs
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise MicroserviceError(f'No se pudo contactar con el servicio de materiales ({exc.__class__.__name__}).') from exc


def list_items():
    data = _request('GET', '/api/items/')
    items = data.get('items', [])
    for item in items:
        item['created_at'] = parse_datetime(item['created_at'])  # para usar |date en la plantilla
    return items


def create_item(title, description, created_by):
    return _request(
        'POST',
        '/api/items/',
        json={'title': title, 'description': description, 'created_by': created_by},
    )
