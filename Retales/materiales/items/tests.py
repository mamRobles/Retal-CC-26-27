import json

from django.test import TestCase, override_settings

from .models import Composicion, Item

TOKEN = 'tokenfalso'
URL = '/api/items/'


@override_settings(SERVICE_TOKEN=TOKEN)
class ItemTestCase(TestCase):
    def _auth(self):
        return {'X-Service-Token': TOKEN}

    def _post(self, payload, headers=None):
        return self.client.post(
            URL,
            data=json.dumps(payload),
            content_type='application/json',
            headers=headers if headers is not None else self._auth(),
        )

    # 401 sin token
    def test_sin_token_devuelve_401(self):
        self.assertEqual(self.client.get(URL).status_code, 401)
        self.assertEqual(self._post({'title': 'x', 'created_by': 'ana'}, headers={}).status_code, 401)

    def test_token_incorrecto_devuelve_401(self):
        response = self.client.get(URL, headers={'X-Service-Token': 'otro'})
        self.assertEqual(response.status_code, 401)

    # GET devuelve la lista
    def test_get_devuelve_lista(self):
        Item.objects.create(titulo='Lana merino', descripcion='Azul', creado_por='ana')
        Item.objects.create(titulo='Ganchillo 4mm', creado_por='ana')

        response = self.client.get(URL, headers=self._auth())

        self.assertEqual(response.status_code, 200)
        items = response.json()['items']
        self.assertEqual(len(items), 2)
        # el contrato JSON está en inglés aunque el modelo esté en español
        self.assertEqual(
            set(items[0]),
            {
                'id', 'title', 'description', 'created_by', 'created_at', 'yarn_weight',
                'yarn_weight_display', 'needle_mm', 'hook_mm', 'brand', 'composition',
            },
        )
        self.assertEqual({i['title'] for i in items}, {'Lana merino', 'Ganchillo 4mm'})

    def test_get_sin_items_devuelve_lista_vacia(self):
        response = self.client.get(URL, headers=self._auth())
        self.assertEqual(response.json(), {'items': []})

    # POST crea un ítem
    def test_post_crea_item(self):
        response = self._post(
            {'title': 'Lana merino', 'description': 'Azul', 'created_by': 'ana'}
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['title'], 'Lana merino')
        self.assertEqual(Item.objects.count(), 1)
        item = Item.objects.get()
        self.assertEqual(item.titulo, 'Lana merino')
        self.assertEqual(item.descripcion, 'Azul')
        self.assertEqual(item.creado_por, 'ana')

    # POST sin título devuelve 400
    def test_post_sin_titulo_devuelve_400(self):
        response = self._post({'description': 'sin título', 'created_by': 'ana'})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Item.objects.count(), 0)

    def test_post_con_titulo_vacio_devuelve_400(self):
        response = self._post({'title': '   ', 'created_by': 'ana'})
        self.assertEqual(response.status_code, 400)

    def test_post_json_invalido_devuelve_400(self):
        response = self.client.post(
            URL, data='{no es json', content_type='application/json', headers=self._auth()
        )
        self.assertEqual(response.status_code, 400)

    def test_health_no_requiere_token(self):
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

@override_settings(SERVICE_TOKEN=TOKEN)
class ComposicionTestCase(TestCase):
    def _post(self, payload):
        return self.client.post(
            URL, data=json.dumps(payload), content_type='application/json',
            headers={'X-Service-Token': TOKEN},
        )

    def test_crear_con_composicion(self):
        response = self._post({
            'title': 'Drops Nepal', 'created_by': 'ana', 'yarn_weight': 'aran',
            'needle_mm': '5.0', 'brand': 'Drops',
            'composition': [{'fiber': 'lana', 'percent': '65'}, {'fiber': 'merino', 'percent': '35'}],
        })
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['yarn_weight'], 'aran')
        self.assertEqual(data['needle_mm'], '5.00')
        self.assertEqual(len(data['composition']), 2)

    def test_porcentajes_que_suman_mas_de_100(self):
        response = self._post({
            'title': 'X', 'created_by': 'ana',
            'composition': [{'fiber': 'lana', 'percent': '80'}, {'fiber': 'seda', 'percent': '30'}],
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Item.objects.exists())  # no queda el item a medias

    def test_fibra_repetida_o_invalida(self):
        repetida = [{'fiber': 'lana', 'percent': '50'}, {'fiber': 'lana', 'percent': '50'}]
        self.assertEqual(self._post({'title': 'X', 'created_by': 'ana', 'composition': repetida}).status_code, 400)
        invalida = [{'fiber': 'oro', 'percent': '50'}]
        self.assertEqual(self._post({'title': 'X', 'created_by': 'ana', 'composition': invalida}).status_code, 400)

    def test_grosor_y_aguja_invalidos(self):
        self.assertEqual(self._post({'title': 'X', 'created_by': 'ana', 'yarn_weight': 'gordo'}).status_code, 400)
        self.assertEqual(self._post({'title': 'X', 'created_by': 'ana', 'needle_mm': '50'}).status_code, 400)

@override_settings(SERVICE_TOKEN=TOKEN)
class ChoicesTestCase(TestCase):
    URL = '/api/choices/'

    def test_sin_token_devuelve_401(self):
        self.assertEqual(self.client.get(self.URL).status_code, 401)

    def test_devuelve_las_opciones_de_los_modelos(self):
        response = self.client.get(self.URL, headers={'X-Service-Token': TOKEN})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            [(o['value'], o['label']) for o in data['yarn_weight']], Item.TamLana.choices
        )
        self.assertEqual(
            [(o['value'], o['label']) for o in data['fiber']], Composicion.Fibra.choices
        )

    def test_solo_admite_get(self):
        response = self.client.post(self.URL, headers={'X-Service-Token': TOKEN})
        self.assertEqual(response.status_code, 405)


@override_settings(SERVICE_TOKEN=TOKEN)
class ItemDetailTestCase(TestCase):
    def setUp(self):
        self.item = Item.objects.create(titulo='Drops Nepal', creado_por='ana')
        self.item.composicion.create(fibra='lana', porcentaje=100)
        self.url = f'/api/items/{self.item.id}/'
        self.auth = {'X-Service-Token': TOKEN}

    def test_sin_token_devuelve_401(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.assertEqual(self.client.delete(self.url).status_code, 401)
        self.assertTrue(Item.objects.filter(pk=self.item.id).exists())

    def test_get_devuelve_el_material(self):
        response = self.client.get(self.url, headers=self.auth)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], 'Drops Nepal')
        self.assertEqual(response.json()['created_by'], 'ana')

    def test_delete_borra_el_material_y_su_composicion(self):
        response = self.client.delete(self.url, headers=self.auth)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Item.objects.filter(pk=self.item.id).exists())
        self.assertFalse(Composicion.objects.filter(item_id=self.item.id).exists())

    def test_inexistente_devuelve_404(self):
        self.assertEqual(self.client.get('/api/items/9999/', headers=self.auth).status_code, 404)
        self.assertEqual(self.client.delete('/api/items/9999/', headers=self.auth).status_code, 404)

@override_settings(SERVICE_TOKEN=TOKEN)
class ItemUpdateTestCase(TestCase):
    def setUp(self):
        self.item = Item.objects.create(titulo='Drops Nepal', creado_por='ana', marca='Drops')
        self.item.composicion.create(fibra='lana', porcentaje=100)
        self.url = f'/api/items/{self.item.id}/'
        self.auth = {'X-Service-Token': TOKEN}

    def put(self, url=None, headers=None, **payload):
        return self.client.put(
            url or self.url,
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.auth if headers is None else headers,
        )

    def test_sin_token_devuelve_401(self):
        response = self.put(headers={}, title='Hackeado')

        self.assertEqual(response.status_code, 401)
        self.item.refresh_from_db()
        self.assertEqual(self.item.titulo, 'Drops Nepal')

    def test_put_cambia_los_campos_y_reemplaza_la_composicion(self):
        response = self.put(
            title='Drops Nepal gris', yarn_weight='aran', needle_mm='5', brand='Drops',
            composition=[{'fiber': 'lana', 'percent': '65'}, {'fiber': 'merino', 'percent': '35'}],
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], 'Drops Nepal gris')
        self.item.refresh_from_db()
        self.assertEqual(self.item.titulo, 'Drops Nepal gris')
        self.assertEqual(self.item.tam_lana, 'aran')
        self.assertEqual(
            sorted(self.item.composicion.values_list('fibra', flat=True)), ['lana', 'merino']
        )

    def test_la_respuesta_trae_la_composicion_nueva(self):
        # Comprueba el refresh_from_db: sin él saldría la composición antigua precargada.
        response = self.put(title='Seda pura', composition=[{'fiber': 'seda', 'percent': '100'}])

        self.assertEqual([c['fiber'] for c in response.json()['composition']], ['seda'])

    def test_composicion_vacia_borra_las_fibras(self):
        self.put(title='Sin composición', composition=[])

        self.assertFalse(self.item.composicion.exists())

    def test_no_se_puede_cambiar_el_dueno(self):
        response = self.put(title='Drops Nepal', created_by='luis')

        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.creado_por, 'ana')

    def test_datos_invalidos_devuelven_400_y_no_cambian_nada(self):
        response = self.put(title='', needle_mm='50')

        self.assertEqual(response.status_code, 400)
        self.assertIn('titulo', response.json()['error'])
        self.item.refresh_from_db()
        self.assertEqual(self.item.titulo, 'Drops Nepal')

    def test_composicion_invalida_deshace_todo_el_cambio(self):
        # El título es válido, pero la composición no: la transacción deshace también el título.
        response = self.put(
            title='Título nuevo',
            composition=[{'fiber': 'lana', 'percent': '80'}, {'fiber': 'seda', 'percent': '30'}],
        )

        self.assertEqual(response.status_code, 400)
        self.item.refresh_from_db()
        self.assertEqual(self.item.titulo, 'Drops Nepal')
        self.assertEqual(list(self.item.composicion.values_list('fibra', flat=True)), ['lana'])

    def test_json_invalido_devuelve_400(self):
        response = self.client.put(
            self.url, data='{no es json', content_type='application/json', headers=self.auth
        )
        self.assertEqual(response.status_code, 400)

    def test_inexistente_devuelve_404(self):
        self.assertEqual(self.put(url='/api/items/9999/', title='X').status_code, 404)
