'''Formularios de materiales.

Los materiales no tienen modelo en Retales: viven en el microservicio. Por eso son
forms.Form normales y las opciones de los desplegables (grosor de lana, fibras) se piden
a la API con services.get_choices() en lugar de copiarlas aquí.

La API vuelve a validarlo todo; estos formularios solo dan errores claros al usuario
antes de hacer la petición.
'''
from decimal import Decimal

from core import services
from django import forms

TAM_MM = {
    'required': False, 'max_digits': 4, 'decimal_places': 2,
    'min_value': Decimal('0.1'), 'max_value': Decimal(20),
}


class MaterialForm(forms.Form):
    titulo = forms.CharField(max_length=200)
    descripcion = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    tam_lana = forms.ChoiceField(label='Grosor de lana')
    tam_aguja_mm = forms.DecimalField(label='Aguja (mm)', **TAM_MM)
    tam_ganchillo_mm = forms.DecimalField(label='Ganchillo (mm)', **TAM_MM)
    marca = forms.CharField(max_length=200, required=False)

    def __init__(self, *args, tam_lana_choices, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tam_lana'].choices = tam_lana_choices

    @staticmethod
    def initial_desde_api(item):
        '''Para editar: traduce un ítem de la API (claves en inglés) a los campos del form.'''
        return {
            'titulo': item['title'],
            'descripcion': item['description'],
            'tam_lana': item['yarn_weight'],
            'tam_aguja_mm': item['needle_mm'],
            'tam_ganchillo_mm': item['hook_mm'],
            'marca': item['brand'],
        }

    def to_api(self):
        '''Traduce al contrato JSON de la API (en inglés, como serialize() del microservicio).'''
        d = self.cleaned_data
        return {
            'title': d['titulo'],
            'description': d['descripcion'],
            'yarn_weight': d['tam_lana'],
            'needle_mm': _decimal_a_str(d['tam_aguja_mm']),
            'hook_mm': _decimal_a_str(d['tam_ganchillo_mm']),
            'brand': d['marca'],
        }


class ComposicionForm(forms.Form):
    fibra = forms.ChoiceField()
    porcentaje = forms.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal('0.01'), max_value=Decimal(100)
    )

    def __init__(self, *args, fibra_choices, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fibra'].choices = [('', '---------'), *fibra_choices]


class BaseComposicionFormSet(forms.BaseFormSet):
    def _filas(self):
        '''Filas rellenas y no marcadas para borrar (las vacías del "extra" se ignoran).'''
        return [
            f.cleaned_data for f in self.forms
            if f.cleaned_data and not f.cleaned_data.get('DELETE')
        ]

    def clean(self):
        if any(self.errors):
            return
        fibras = [fila['fibra'] for fila in self._filas()]
        if len(fibras) != len(set(fibras)):
            raise forms.ValidationError('No repitas la misma fibra.')
        if sum(fila['porcentaje'] for fila in self._filas()) > 100:
            raise forms.ValidationError('Los porcentajes suman más de 100.')

    def to_api(self):
        return [
            {'fiber': fila['fibra'], 'percent': str(fila['porcentaje'])}
            for fila in self._filas()
        ]

    @staticmethod
    def initial_desde_api(item):
        return [
            {'fibra': c['fiber'], 'porcentaje': c['percent']} for c in item['composition']
        ]


ComposicionFormSet = forms.formset_factory(
    ComposicionForm, formset=BaseComposicionFormSet, extra=1, can_delete=True
)


def formularios_material(data=None, item=None):
    '''Construye el form y el formset de composición con las opciones de la API.

    - data: request.POST al enviar.
    - item: el material tal y como lo devuelve la API, para precargar al editar.

    Lanza services.MicroserviceError si no se pueden obtener las opciones; la vista
    decide qué mostrar en ese caso.
    '''
    choices = services.get_choices()
    form = MaterialForm(
        data,
        initial=MaterialForm.initial_desde_api(item) if item else None,
        tam_lana_choices=choices['yarn_weight'],
    )
    formset = ComposicionFormSet(
        data,
        initial=BaseComposicionFormSet.initial_desde_api(item) if item else None,
        prefix='composicion',
        form_kwargs={'fibra_choices': choices['fiber']},
    )
    return form, formset


def payload_material(form, formset):
    '''JSON completo para create_item/update_item a partir de form y formset ya validados.'''
    return {**form.to_api(), 'composition': formset.to_api()}


def errores_api_en_form(form, exc):
    """Pasa los errores de un 400 de la API al formulario.

    Los campos del form se llaman igual que los del modelo de la API, así que cada
    error cae en su campo; el resto (composición, errores generales) va arriba.
    """
    if not exc.errores:
        form.add_error(None, str(exc))
        return
    for campo, mensajes in exc.errores.items():
        destino = campo if campo in form.fields else None
        for mensaje in mensajes:
            form.add_error(destino, mensaje)


def _decimal_a_str(valor):
    return str(valor) if valor is not None else None
