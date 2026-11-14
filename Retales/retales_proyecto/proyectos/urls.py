from django.urls import path

from . import views

urlpatterns = [
    path('', views.ProyectoListView.as_view(), name='proyecto_list'),
    path('agregar/', views.ProyectoCreateView.as_view(), name='proyecto_agregar'),
    path('<int:pk>/', views.ProyectoDetailView.as_view(), name='proyecto_detalle'),
    path('<int:pk>/edit/', views.ProyectoUpdateView.as_view(), name='proyecto_editar'),
    path('<int:pk>/delete/', views.ProyectoDeleteView.as_view(), name='proyecto_borrar'),
]