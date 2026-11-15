from core import services
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, TemplateView

from .forms import SignupForm


@require_http_methods(["GET", "POST"])
def registro(request):
    form = SignupForm(
        request.POST if request.method == "POST" else None
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("login")
    return render(request, "registro.html", {"form": form})


class PerfilView(DetailView):
    """/<username>/ : perfil público del usuario con sus proyectos visibles."""

    model = get_user_model()
    slug_field = 'username'
    slug_url_kwarg = 'username'
    template_name = 'users/perfil.html'
    context_object_name = 'perfil'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        es_propietario = self.request.user == self.object
        proyectos = self.object.proyectos.all()
        ctx['es_propietario'] = es_propietario
        ctx['proyectos'] = proyectos if es_propietario else proyectos.filter(publico=True)
        return ctx


class MaterialesView(TemplateView):
    """/<username>/materiales/ : materiales del usuario, pedidos al microservicio."""

    template_name = 'users/materiales.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        propietario = get_object_or_404(get_user_model(), username=kwargs['username'])
        ctx['propietario'] = propietario
        try:
            ctx['materiales'] = [
                i for i in services.list_items() if i['created_by'] == propietario.username
            ]
        except services.MicroserviceError as exc:
            # Si materiales está caído, la página sigue funcionando y avisa.
            ctx['materiales'] = []
            ctx['error'] = str(exc)
        return ctx
