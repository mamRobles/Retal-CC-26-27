from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render


def health(request):
    return HttpResponse('ok')


def base_view(request):
    return render(request, 'home.html')


@login_required
def dashboard(request):
    """Destino tras el login (LOGIN_REDIRECT_URL): lleva a tu propio perfil."""
    return redirect('perfil', username=request.user.username)
