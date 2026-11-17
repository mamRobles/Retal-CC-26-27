import json

from django.test import TestCase, override_settings

from .models import Item

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