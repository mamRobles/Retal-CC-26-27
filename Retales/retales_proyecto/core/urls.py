from django.urls import path

from . import views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('panel/', views.dashboard, name='dashboard'),
    path('', views.base_view, name='home'),
]
