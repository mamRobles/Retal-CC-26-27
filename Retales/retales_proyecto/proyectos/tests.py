from unittest.mock import patch

from core import services
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Proyecto

User = get_user_model()


class ProyectoViewsTestCase(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user('ana', 'ana@example.com', 'clave-segura-123')
        self.luis = User.objects.create_user('luis', 'luis@example.com', 'clave-segura-123')
        self.publico = Proyecto.objects.create(usuario=self.ana, titulo='Jersey', publico=True)
        self.privado = Proyecto.objects.create(usuario=self.ana, titulo='Bufanda secreta')
        # Crear/editar piden los materiales al microservicio: aquí no hay ninguno.
        patcher = patch('core.services.list_items', return_value=[])
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_la_portada_carga(self):
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)

    def test_login_y_registro_cargan(self):
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)
        self.assertEqual(self.client.get(reverse('registro')).status_code, 200)

    def test_tras_login_redirige_al_perfil(self):
        response = self.client.post(
            reverse('login'), {'username': 'ana', 'password': 'clave-segura-123'}, follow=True
        )
        self.assertRedirects(response, reverse('perfil', args=['ana']))

    def test_el_propietario_ve_todos_sus_proyectos(self):
        self.client.force_login(self.ana)
        response = self.client.get(reverse('proyecto_list', args=['ana']))
        self.assertContains(response, 'Jersey')
        self.assertContains(response, 'Bufanda secreta')

    def test_otros_solo_ven_los_publicos(self):
        self.client.force_login(self.luis)
        response = self.client.get(reverse('proyecto_list', args=['ana']))
        self.assertContains(response, 'Jersey')
        self.assertNotContains(response, 'Bufanda secreta')
        detalle = reverse('proyecto_detalle', args=['ana', self.privado.pk])
        self.assertEqual(self.client.get(detalle).status_code, 404)

    def test_crear_proyecto(self):
        self.client.force_login(self.ana)
        response = self.client.post(
            reverse('proyecto_agregar', args=['ana']),
            {'titulo': 'Gorro', 'tecnica': 'ganchillo', 'estado': 'en_curso', 'progreso': 30},
        )
        self.assertRedirects(response, reverse('proyecto_list', args=['ana']))
        self.assertTrue(Proyecto.objects.filter(usuario=self.ana, titulo='Gorro').exists())

    def test_crear_exige_login(self):
        response = self.client.get(reverse('proyecto_agregar', args=['ana']))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_no_se_puede_editar_ni_borrar_lo_ajeno(self):
        self.client.force_login(self.luis)
        editar = reverse('proyecto_editar', args=['ana', self.publico.pk])
        borrar = reverse('proyecto_borrar', args=['ana', self.publico.pk])
        self.assertEqual(self.client.post(editar, {'titulo': 'hackeado'}).status_code, 404)
        self.assertEqual(self.client.post(borrar).status_code, 404)
        self.assertTrue(Proyecto.objects.filter(pk=self.publico.pk).exists())

    def test_editar_y_borrar_propio(self):
        self.client.force_login(self.ana)
        self.client.post(
            reverse('proyecto_editar', args=['ana', self.publico.pk]),
            {'titulo': 'Jersey azul', 'tecnica': 'punto', 'estado': 'terminado', 'progreso': 100},
        )
        self.publico.refresh_from_db()
        self.assertEqual(self.publico.titulo, 'Jersey azul')
        self.client.post(reverse('proyecto_borrar', args=['ana', self.publico.pk]))
        self.assertFalse(Proyecto.objects.filter(pk=self.publico.pk).exists())

    def test_progreso_no_puede_pasar_de_100(self):
        self.client.force_login(self.ana)
        response = self.client.post(
            reverse('proyecto_agregar', args=['ana']),
            {'titulo': 'X', 'tecnica': 'punto', 'estado': 'planeado', 'progreso': 150},
        )
        self.assertEqual(response.status_code, 200)  # vuelve al formulario con error
        self.assertFalse(Proyecto.objects.filter(titulo='X').exists())

    def test_buscador_solo_muestra_publicos(self):
        response = self.client.get(reverse('busqueda'), {'q': 'e'})
        self.assertContains(response, 'Jersey')
        self.assertNotContains(response, 'Bufanda secreta')

    def test_perfil_de_usuario_inexistente_da_404(self):
        self.assertEqual(self.client.get('/nadie/').status_code, 404)


class RegistroTestCase(TestCase):
    def test_nombre_reservado_no_se_puede_usar(self):
        response = self.client.post(reverse('registro'), {
            'username': 'admin', 'email': 'a@example.com',
            'password1': 'clave-segura-123', 'password2': 'clave-segura-123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='admin').exists())


MATERIALES_ANA = [
    {'id': 1, 'title': 'Drops Nepal', 'yarn_weight_display': 'Aran (CYC 4)', 'brand': 'Drops'},
    {'id': 2, 'title': 'Algodón azul', 'yarn_weight_display': 'DK (CYC 3)', 'brand': ''},
    {'id': 3, 'title': 'Merino gris', 'yarn_weight_display': 'Sport (CYC 2)', 'brand': ''},
]
DATOS_PROYECTO = {'titulo': 'Jersey', 'tecnica': 'punto', 'estado': 'en_curso', 'progreso': 10}


@patch('core.services.list_items', return_value=MATERIALES_ANA)
class EnlazarMaterialesTestCase(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user('ana', 'ana@example.com', 'clave-segura-123')
        self.luis = User.objects.create_user('luis', 'luis@example.com', 'clave-segura-123')
        self.client.force_login(self.ana)
        self.agregar = reverse('proyecto_agregar', args=['ana'])

    def test_el_form_ofrece_los_materiales_del_usuario(self, mock_list):
        response = self.client.get(self.agregar)

        mock_list.assert_called_once_with(created_by='ana')
        self.assertContains(response, 'Drops Nepal')
        self.assertContains(response, 'type="checkbox" name="materiales_ids" value="1"')

    def test_crear_con_materiales_guarda_los_ids_como_numeros(self, _):
        self.client.post(self.agregar, {**DATOS_PROYECTO, 'materiales_ids': ['1', '3']})

        proyecto = Proyecto.objects.get(titulo='Jersey')
        self.assertEqual(proyecto.materiales_ids, [1, 3])

    def test_no_se_puede_enlazar_un_material_que_no_es_tuyo(self, _):
        # El 99 no está entre los materiales de Ana (p. ej. es de Luis).
        response = self.client.post(self.agregar, {**DATOS_PROYECTO, 'materiales_ids': ['99']})

        self.assertEqual(response.status_code, 200)
        self.assertIn('materiales_ids', response.context['form'].errors)
        self.assertFalse(Proyecto.objects.filter(titulo='Jersey').exists())

    def test_editar_precarga_y_cambia_los_enlaces(self, _):
        proyecto = Proyecto.objects.create(usuario=self.ana, titulo='Gorro', materiales_ids=[1])
        url = reverse('proyecto_editar', args=['ana', proyecto.pk])

        self.assertEqual(self.client.get(url).context['form'].initial['materiales_ids'], [1])

        self.client.post(url, {**DATOS_PROYECTO, 'titulo': 'Gorro', 'materiales_ids': ['2']})
        proyecto.refresh_from_db()
        self.assertEqual(proyecto.materiales_ids, [2])

    def test_desmarcar_todo_deja_la_lista_vacia(self, _):
        proyecto = Proyecto.objects.create(usuario=self.ana, titulo='Gorro', materiales_ids=[1, 2])

        self.client.post(reverse('proyecto_editar', args=['ana', proyecto.pk]), {**DATOS_PROYECTO, 'titulo': 'Gorro'})

        proyecto.refresh_from_db()
        self.assertEqual(proyecto.materiales_ids, [])

    def test_si_la_api_cae_se_puede_guardar_y_se_conservan_los_enlaces(self, mock_list):
        mock_list.side_effect = services.MicroserviceError('caído')
        proyecto = Proyecto.objects.create(usuario=self.ana, titulo='Gorro', materiales_ids=[1, 2])
        url = reverse('proyecto_editar', args=['ana', proyecto.pk])

        response = self.client.get(url)
        self.assertContains(response, 'no se pueden cargar tus materiales')
        self.assertNotIn('materiales_ids', response.context['form'].fields)

        self.client.post(url, {**DATOS_PROYECTO, 'titulo': 'Gorro con pompón'})
        proyecto.refresh_from_db()
        self.assertEqual(proyecto.titulo, 'Gorro con pompón')
        self.assertEqual(proyecto.materiales_ids, [1, 2])  # no se han perdido


@patch('core.services.list_items', return_value=MATERIALES_ANA)
class DetalleConMaterialesTestCase(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user('ana', 'ana@example.com', 'clave-segura-123')

    def detalle(self, proyecto):
        return self.client.get(reverse('proyecto_detalle', args=['ana', proyecto.pk]))

    def test_muestra_solo_los_materiales_enlazados(self, mock_list):
        proyecto = Proyecto.objects.create(
            usuario=self.ana, titulo='Jersey', publico=True, materiales_ids=[1, 3]
        )

        response = self.detalle(proyecto)  # visitante anónimo: el proyecto es público

        mock_list.assert_called_once_with(created_by='ana')
        self.assertContains(response, 'Drops Nepal')
        self.assertContains(response, 'Merino gris')
        self.assertNotContains(response, 'Algodón azul')

    def test_sin_materiales_no_llama_a_la_api(self, mock_list):
        proyecto = Proyecto.objects.create(usuario=self.ana, titulo='Jersey', publico=True)

        response = self.detalle(proyecto)

        self.assertEqual(response.status_code, 200)
        mock_list.assert_not_called()

    def test_si_la_api_cae_el_detalle_carga_y_avisa(self, mock_list):
        mock_list.side_effect = services.MicroserviceError('No se pudo contactar.')
        proyecto = Proyecto.objects.create(
            usuario=self.ana, titulo='Jersey', publico=True, materiales_ids=[1]
        )

        response = self.detalle(proyecto)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No se pudo contactar.')


class BusquedaFiltrosTestCase(TestCase):
    def setUp(self):
        ana = User.objects.create_user('ana', 'ana@example.com', 'clave-segura-123')
        crear = Proyecto.objects.create
        crear(usuario=ana, titulo='Jersey de punto', tecnica='punto', estado='en_curso', publico=True)
        crear(usuario=ana, titulo='Gorro de ganchillo', tecnica='ganchillo', estado='terminado', publico=True)
        crear(usuario=ana, titulo='Amigurumi', tecnica='ganchillo', estado='en_curso', publico=True)
        crear(usuario=ana, titulo='Ganchillo secreto', tecnica='ganchillo', estado='en_curso')  # privado

    def titulos(self, **params):
        response = self.client.get(reverse('busqueda'), params)
        self.assertEqual(response.status_code, 200)
        return sorted(p.titulo for p in response.context['proyectos'])

    def test_filtra_por_tecnica(self):
        self.assertEqual(self.titulos(tecnica='ganchillo'), ['Amigurumi', 'Gorro de ganchillo'])

    def test_filtra_por_estado(self):
        self.assertEqual(self.titulos(estado='en_curso'), ['Amigurumi', 'Jersey de punto'])

    def test_filtros_combinados_con_texto(self):
        self.assertEqual(self.titulos(q='gorro', tecnica='ganchillo', estado='terminado'), ['Gorro de ganchillo'])
        self.assertEqual(self.titulos(tecnica='punto', estado='terminado'), [])

    def test_los_privados_no_salen_aunque_coincidan(self):
        self.assertNotIn('Ganchillo secreto', self.titulos(tecnica='ganchillo', estado='en_curso'))

    def test_un_valor_que_no_existe_se_ignora(self):
        self.assertEqual(len(self.titulos(tecnica='macrame', estado='???')), 3)

    def test_el_desplegable_recuerda_lo_elegido(self):
        response = self.client.get(reverse('busqueda'), {'tecnica': 'ganchillo'})
        self.assertContains(response, '<option value="ganchillo" selected>')

    def test_la_paginacion_conserva_los_filtros(self):
        ana = User.objects.get(username='ana')
        Proyecto.objects.bulk_create(
            Proyecto(usuario=ana, titulo=f'Chal {n}', tecnica='ganchillo', publico=True)
            for n in range(25)
        )

        response = self.client.get(reverse('busqueda'), {'q': 'chal', 'tecnica': 'ganchillo'})

        self.assertContains(response, '?q=chal&amp;tecnica=ganchillo&amp;page=2')
        siguiente = self.client.get(reverse('busqueda'), {'q': 'chal', 'tecnica': 'ganchillo', 'page': 2})
        self.assertEqual(len(siguiente.context['proyectos']), 5)  # 25 = 20 + 5
