from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.PerfilView.as_view(), name='perfil'),
    path('materiales/', views.MaterialesView.as_view(), name='materiales'),
    path('proyectos/', include('proyectos.urls')),
]