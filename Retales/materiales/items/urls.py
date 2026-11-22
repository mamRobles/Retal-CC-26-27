from django.urls import path

from . import views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('api/items/', views.items, name='items'),
    path('api/items/<int:item_id>/', views.item_detail, name='item_detail'),
    path('api/choices/', views.choices, name='choices'),
]
