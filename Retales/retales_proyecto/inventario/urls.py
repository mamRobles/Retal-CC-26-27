from django.urls import path

from . import views

# Se incluye desde users/urls.py bajo /<username>/materiales/
urlpatterns = [
    path('', views.MaterialListView.as_view(), name='materiales'),
    path('agregar/', views.MaterialCreateView.as_view(), name='material_agregar'),
    path('<int:item_id>/borrar/', views.MaterialDeleteView.as_view(), name='material_borrar'),
    path('<int:item_id>/editar/', views.MaterialUpdateView.as_view(), name='material_editar'),
]
