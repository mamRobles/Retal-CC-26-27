from core.widgets import CasillaNeon, CasillasNeon
from django import forms

from .models import Proyecto


class ProyectoForm(forms.ModelForm):
    # Los materiales viven en el microservicio: aquí solo se guardan sus ids.
    # Las opciones las pone __init__ con los materiales del usuario.
    materiales_ids = forms.TypedMultipleChoiceField(
        label='Materiales',
        coerce=int,  # los ids llegan del POST como texto; en el JSONField se guardan como números
        required=False,
        widget=CasillasNeon,
    )

    publico = forms.BooleanField(label='Público', required=False, widget=CasillaNeon)

    class Meta:
        model = Proyecto
        # 'usuario' lo pone la vista (el usuario logueado), nunca el formulario.
        fields = (
            'titulo', 'descripcion', 'tecnica', 'estado', 'progreso',
            'notas', 'opinion', 'publico', 'materiales_ids',
        )

    def __init__(self, *args, materiales=None, **kwargs):
        '''materiales: lista de (id, título) con los materiales del usuario, o None si
        el microservicio no respondió. En ese caso se quita el campo: el proyecto se
        puede guardar igual y conserva los materiales que ya tuviera enlazados.'''
        super().__init__(*args, **kwargs)
        self.materiales_no_disponibles = materiales is None
        if materiales is None:
            del self.fields['materiales_ids']
        else:
            self.fields['materiales_ids'].choices = materiales