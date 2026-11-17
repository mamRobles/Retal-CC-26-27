
from unittest.mock import MagicMock, patch
 
import requests
from django.test import SimpleTestCase, TestCase, override_settings
 
from core import services
 
 
class HealthTestCase(TestCase):
    def test_health_devuelve_ok(self):
        response = self.client.get('/health/')
 
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'ok')
 
 
@override_settings(MICROSERVICE_URL='http://materiales:8000', SERVICE_TOKEN='tok')
@patch('core.services.requests.request')
class CoreServicesTestCase(SimpleTestCase):
    def _respuesta(self, datos):
        response = MagicMock()
        response.json.return_value = datos
        return response
 
    def test_list_items_llama_al_microservicio_con_token(self, mock_request):
        mock_request.return_value = self._respuesta({'items': []})
 
        resultado = services.list_items()
 
        self.assertEqual(resultado, [])
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(args, ('GET', 'http://materiales:8000/api/items/'))
        self.assertEqual(kwargs['headers'], {'X-Service-Token': 'tok'})
 
    def test_list_items_convierte_created_at_a_datetime(self, mock_request):
        mock_request.return_value = self._respuesta(
            {'items': [{'id': 1, 'title': 'Lana', 'created_at': '2026-11-14T10:30:00+01:00'}]}
        )
 
        items = services.list_items()
 
        self.assertEqual(items[0]['title'], 'Lana')
        self.assertEqual(items[0]['created_at'].year, 2026)
        self.assertEqual(items[0]['created_at'].hour, 10)
 
    def test_create_item_envia_json_por_post(self, mock_request):
        mock_request.return_value = self._respuesta({'id': 7, 'title': 'Lana'})
 
        resultado = services.create_item('Lana', 'Azul', 'ana')
 
        self.assertEqual(resultado['id'], 7)
        args, kwargs = mock_request.call_args
        self.assertEqual(args, ('POST', 'http://materiales:8000/api/items/'))
        self.assertEqual(
            kwargs['json'], {'title': 'Lana', 'description': 'Azul', 'created_by': 'ana'}
        )
 
    def test_error_de_red_lanza_microservice_error(self, mock_request):
        mock_request.side_effect = requests.ConnectionError('caído')
 
        with self.assertRaises(services.MicroserviceError):
            services.list_items()
 
    def test_respuesta_http_de_error_lanza_microservice_error(self, mock_request):
        response = MagicMock()
        response.raise_for_status.side_effect = requests.HTTPError('401')
        mock_request.return_value = response
 
        with self.assertRaises(services.MicroserviceError):
            services.create_item('Lana', '', 'ana')
 