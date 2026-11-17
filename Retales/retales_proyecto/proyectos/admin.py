from django.contrib import admin

from .models import Proyecto


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'usuario', 'tecnica', 'estado', 'progreso', 'publico', 'actualizado')
    list_filter = ('tecnica', 'estado', 'publico')
    search_fields = ('titulo', 'descripcion', 'usuario__username')
