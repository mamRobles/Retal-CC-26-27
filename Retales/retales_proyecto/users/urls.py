from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.PerfilView.as_view(), name='perfil'),
    path('materiales/', include('inventario.urls')),
    path('proyectos/', include('proyectos.urls')),
]