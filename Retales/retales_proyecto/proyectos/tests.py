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
