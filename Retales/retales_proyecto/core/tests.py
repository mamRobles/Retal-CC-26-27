
from unittest.mock import MagicMock, patch
 
import requests
from django.core.cache import cache
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
 
    def test_un_400_trae_los_errores_por_campo(self, mock_request):
        error = requests.HTTPError('400')
        error.response = MagicMock(status_code=400)
        error.response.json.return_value = {'error': {'tam_aguja_mm': ['Demasiado grande.']}}
        response = MagicMock()
        response.raise_for_status.side_effect = error
        mock_request.return_value = response

        with self.assertRaises(services.MicroserviceError) as ctx:
            services.create_item('Lana', '', 'ana', needle_mm='50')

        self.assertEqual(ctx.exception.errores, {'tam_aguja_mm': ['Demasiado grande.']})

    def test_un_400_con_mensaje_simple_va_a_errores_generales(self, mock_request):
        error = requests.HTTPError('400')
        error.response = MagicMock(status_code=400)
        error.response.json.return_value = {'error': 'JSON inválido'}
        response = MagicMock()
        response.raise_for_status.side_effect = error
        mock_request.return_value = response

        with self.assertRaises(services.MicroserviceError) as ctx:
            services.create_item('Lana', '', 'ana')

        self.assertEqual(ctx.exception.errores, {'__all__': ['JSON inválido']})


RESPUESTA_CHOICES = {
    'yarn_weight': [{'value': 'dk', 'label': 'DK (CYC 3)'}],
    'fiber': [{'value': 'lana', 'label': 'Lana'}, {'value': 'seda', 'label': 'Seda'}],
}


@override_settings(MICROSERVICE_URL='http://materiales:8000', SERVICE_TOKEN='tok')
@patch('core.services.requests.request')
class GetChoicesTestCase(SimpleTestCase):

    def setUp(self):
        cache.delete(services.CHOICES_CACHE_KEY)

    def _respuesta(self):
        response = MagicMock()
        response.json.return_value = RESPUESTA_CHOICES
        return response

    def test_convierte_al_formato_de_choicefield(self, mock_request):
        mock_request.return_value = self._respuesta()

        choices = services.get_choices()

        self.assertEqual(mock_request.call_args.args, ('GET', 'http://materiales:8000/api/choices/'))
        self.assertEqual(choices['yarn_weight'], [('dk', 'DK (CYC 3)')])
        self.assertEqual(choices['fiber'], [('lana', 'Lana'), ('seda', 'Seda')])

    def test_se_cachea_y_solo_llama_una_vez(self, mock_request):
        mock_request.return_value = self._respuesta()

        services.get_choices()
        services.get_choices()

        mock_request.assert_called_once()

    def test_si_el_servicio_cae_lanza_microservice_error(self, mock_request):
        mock_request.side_effect = requests.ConnectionError('caído')

        with self.assertRaises(services.MicroserviceError):
            services.get_choices()


@override_settings(MICROSERVICE_URL='http://materiales:8000', SERVICE_TOKEN='tok')
@patch('core.services.requests.request')
class ItemDetailServicesTestCase(SimpleTestCase):
    def test_delete_item_llama_a_la_api_y_acepta_204_sin_cuerpo(self, mock_request):
        response = MagicMock(status_code=204)
        response.json.side_effect = ValueError('sin cuerpo')  # como un 204 real
        mock_request.return_value = response

        self.assertIsNone(services.delete_item(7))
        self.assertEqual(mock_request.call_args.args, ('DELETE', 'http://materiales:8000/api/items/7/'))

    def test_get_item_parsea_la_fecha(self, mock_request):
        response = MagicMock(status_code=200)
        response.json.return_value = {'id': 7, 'created_at': '2026-11-22T10:00:00+00:00'}
        mock_request.return_value = response

        item = services.get_item(7)

        self.assertEqual(mock_request.call_args.args, ('GET', 'http://materiales:8000/api/items/7/'))
        self.assertEqual(item['created_at'].year, 2026)

    def test_un_404_lanza_material_no_encontrado(self, mock_request):
        error = requests.HTTPError('404')
        error.response = MagicMock(status_code=404)
        response = MagicMock()
        response.raise_for_status.side_effect = error
        mock_request.return_value = response

        with self.assertRaises(services.MaterialNoEncontrado):
            services.get_item(9999)
