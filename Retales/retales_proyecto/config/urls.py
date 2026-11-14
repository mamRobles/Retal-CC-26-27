'''
URL configuration for retales_proyecto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
'''
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from proyectos import views as proyectos_views
from users import views as users_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cuenta/', include('django.contrib.auth.urls')),   # login/logout/password_change/reset
    path('registro/', users_views.registro, name='registro'),
    path('buscar/', proyectos_views.BusquedaView.as_view(), name='busqueda'),
    path('', include('core.urls')),  # /health/ (lo usa el healthcheck de Docker)
    path('<str:username>/', include('users.urls')), #todos los usuarios existentes

]
if settings.BROWSER_RELOAD:
    # URLs de django_browser_reload (solo en desarrollo)
    urlpatterns += [
        path('__reload__/', include('django_browser_reload.urls')),
    ]