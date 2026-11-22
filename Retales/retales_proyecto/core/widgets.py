'''Widgets de formulario con el estilo propio de Retales.

Las plantillas están en theme/templates/widgets/. El renderer de formularios de Django
las encuentra porque 'theme' es una app instalada (APP_DIRS).
'''
from django import forms


class CasillaNeon(forms.CheckboxInput):
    '''Una casilla suelta (p. ej. "Público", "Quitar") con el estilo neón.'''

    template_name = 'widgets/casilla_neon.html'


class CasillasNeon(forms.CheckboxSelectMultiple):
    '''Lista de casillas (p. ej. materiales de un proyecto) con el estilo neón.'''

    option_template_name = 'widgets/casilla_neon_opcion.html'
