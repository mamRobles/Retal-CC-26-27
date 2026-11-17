from django import forms

from .models import Proyecto


class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        # 'usuario' lo pone la vista (el usuario logueado), nunca el formulario.
        # 'materiales_ids' se gestionará cuando se enlacen materiales del microservicio.
        fields = (
            'titulo', 'descripcion', 'tecnica', 'estado', 'progreso',
            'notas', 'opinion', 'publico',
        )
