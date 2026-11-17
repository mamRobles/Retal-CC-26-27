from unittest.mock import patch

from core import services
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .forms import formularios_material, payload_material

User = get_user_model()

CHOICES = {
    'yarn_weight': [('dk', 'DK (CYC 3)'), ('aran', 'Aran (CYC 4)')],
    'fiber': [('lana', 'Lana'), ('seda', 'Seda'), ('merino', 'Merino')],
}

GESTION = {
    'composicion-TOTAL_FORMS': '3',
    'composicion-INITIAL_FORMS': '0',
    'composicion-MIN_NUM_FORMS': '0',
    'composicion-MAX_NUM_FORMS': '1000',
}


def datos(**extra):
    return {'titulo': 'Drops Nepal', 'tam_lana': 'aran', **GESTION, **extra}


@patch('inventario.forms.services.get_choices', return_value=CHOICES)
class MaterialFormTestCase(SimpleTestCase):
    def test_las_opciones_vienen_de_la_api(self, _):
        form, formset = formularios_material()

        self.assertEqual(form.fields['tam_lana'].choices, CHOICES['yarn_weight'])
        self.assertEqual(formset.forms[0].fields['fibra'].choices[1:], CHOICES['fiber'])

    def test_payload_valido_en_el_contrato_de_la_api(self, _):
        form, formset = formularios_material(datos(**{
            'tam_aguja_mm': '5', 'marca': 'Drops',
            'composicion-0-fibra': 'lana', 'composicion-0-porcentaje': '65',
            'composicion-1-fibra': 'merino', 'composicion-1-porcentaje': '35',
        }))

        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(formset.is_valid(), formset.non_form_errors())
        self.assertEqual(payload_material(form, formset), {
            'title': 'Drops Nepal', 'description': '', 'yarn_weight': 'aran',
            'needle_mm': '5', 'hook_mm': None, 'brand': 'Drops',
            'composition': [
                {'fiber': 'lana', 'percent': '65'}, {'fiber': 'merino', 'percent': '35'},
            ],
        })

    def test_grosor_que_no_esta_en_la_api_no_vale(self, _):
        form, _formset = formularios_material(datos(tam_lana='gordo'))
        self.assertIn('tam_lana', form.errors)

    def test_porcentajes_que_suman_mas_de_100(self, _):
        _form, formset = formularios_material(datos(**{
            'composicion-0-fibra': 'lana', 'composicion-0-porcentaje': '80',
            'composicion-1-fibra': 'seda', 'composicion-1-porcentaje': '30',
        }))
        self.assertFalse(formset.is_valid())

    def test_fibra_repetida(self, _):
        _form, formset = formularios_material(datos(**{
            'composicion-0-fibra': 'lana', 'composicion-0-porcentaje': '50',
            'composicion-1-fibra': 'lana', 'composicion-1-porcentaje': '50',
        }))
        self.assertFalse(formset.is_valid())

    def test_precarga_al_editar(self, _):
        item = {
            'title': 'Nepal', 'description': 'gris', 'yarn_weight': 'aran',
            'needle_mm': '5.00', 'hook_mm': None, 'brand': 'Drops',
            'composition': [{'fiber': 'lana', 'percent': '65.00'}],
        }

        form, formset = formularios_material(item=item)

        self.assertEqual(form.initial['titulo'], 'Nepal')
        self.assertEqual(formset.forms[0].initial, {'fibra': 'lana', 'porcentaje': '65.00'})


class MaterialFormSinServicioTestCase(SimpleTestCase):
    @patch('inventario.forms.services.get_choices', side_effect=services.MicroserviceError('caído'))
    def test_si_la_api_cae_se_propaga_el_error(self, _):
        with self.assertRaises(services.MicroserviceError):
            formularios_material()


ITEM_ANA = {
    'id': 1, 'title': 'Drops Nepal', 'description': '', 'created_by': 'ana',
    'created_at': None, 'yarn_weight': 'aran', 'yarn_weight_display': 'Aran (CYC 4)',
    'needle_mm': '5.00', 'hook_mm': None, 'brand': 'Drops',
    'composition': [{'fiber': 'lana', 'fiber_display': 'Lana', 'percent': '100.00'}],
}
ITEM_LUIS = {**ITEM_ANA, 'id': 2, 'title': 'Algodón de Luis', 'created_by': 'luis'}


@patch('core.services.get_choices', return_value=CHOICES)
class MaterialCreateViewTestCase(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user('ana', 'ana@example.com', 'clave-segura-123')
        self.luis = User.objects.create_user('luis', 'luis@example.com', 'clave-segura-123')
        self.url = reverse('material_agregar', args=['ana'])

    def test_exige_login(self, _):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_no_se_puede_crear_en_la_cuenta_de_otro(self, _):
        self.client.force_login(self.luis)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_el_form_muestra_las_opciones_de_la_api(self, _):
        self.client.force_login(self.ana)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aran (CYC 4)')
        self.assertContains(response, 'Merino')
        self.assertContains(response, '__prefix__')  # plantilla para "Añadir fibra"

    @patch('core.services.create_item', return_value={'id': 1})
    def test_crear_envia_a_la_api_y_redirige(self, mock_create, _):
        self.client.force_login(self.ana)
        response = self.client.post(self.url, datos(**{
            'composicion-0-fibra': 'lana', 'composicion-0-porcentaje': '100',
        }))

        self.assertRedirects(response, reverse('materiales', args=['ana']), fetch_redirect_response=False)
        kwargs = mock_create.call_args.kwargs
        self.assertEqual(kwargs['created_by'], 'ana')  # siempre el logueado, nunca del form
        self.assertEqual(kwargs['title'], 'Drops Nepal')
        self.assertEqual(kwargs['composition'], [{'fiber': 'lana', 'percent': '100'}])

    @patch('core.services.create_item')
    def test_form_invalido_no_llama_a_la_api(self, mock_create, _):
        self.client.force_login(self.ana)
        response = self.client.post(self.url, datos(titulo=''))
        self.assertEqual(response.status_code, 200)
        mock_create.assert_not_called()

    @patch('core.services.create_item')
    def test_errores_400_de_la_api_salen_en_su_campo(self, mock_create, _):
        mock_create.side_effect = services.MicroserviceError(
            'rechazado', {'marca': ['Marca no válida.'], 'fibra': ['Fibra rara.']}
        )
        self.client.force_login(self.ana)

        response = self.client.post(self.url, datos(marca='???'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].errors['marca'], ['Marca no válida.'])
        self.assertIn('Fibra rara.', response.context['form'].non_field_errors())

    def test_si_la_api_cae_se_avisa_sin_romper(self, mock_choices):
        mock_choices.side_effect = services.MicroserviceError('No se pudo contactar.')
        self.client.force_login(self.ana)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 503)
        self.assertContains(response, 'No se pudo contactar.', status_code=503)
        self.assertNotIn('form', response.context)


@patch('core.services.list_items', return_value=[ITEM_ANA, ITEM_LUIS])
class MaterialListViewTestCase(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user('ana', 'ana@example.com', 'clave-segura-123')
        self.url = reverse('materiales', args=['ana'])

    def test_solo_salen_los_del_usuario(self, _):
        response = self.client.get(self.url)
        self.assertContains(response, 'Drops Nepal')
        self.assertNotContains(response, 'Algodón de Luis')

    def test_el_boton_de_nuevo_solo_lo_ve_el_dueno(self, _):
        boton = reverse('material_agregar', args=['ana'])
        self.assertNotContains(self.client.get(self.url), boton)
        self.client.force_login(self.ana)
        self.assertContains(self.client.get(self.url), boton)
