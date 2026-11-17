from core import services
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView

from .forms import errores_api_en_form, formularios_material, payload_material


class SoloPropietarioMixin(LoginRequiredMixin):
    '''Hay que estar logueado y ser el dueño de /<username>/materiales/...
    Si no lo eres, 404 (igual que en proyectos: no revelamos nada).'''

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.username != kwargs['username']:
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class MaterialListView(TemplateView):
    '''/<username>/materiales/ : materiales del usuario, pedidos al microservicio.'''

    template_name = 'inventario/material_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        propietario = get_object_or_404(get_user_model(), username=kwargs['username'])
        ctx['propietario'] = propietario
        ctx['es_propietario'] = self.request.user == propietario
        try:
            ctx['materiales'] = [
                i for i in services.list_items() if i['created_by'] == propietario.username
            ]
        except services.MicroserviceError as exc:
            # Si materiales está caído, la página sigue funcionando y avisa.
            ctx['materiales'] = []
            ctx['error'] = str(exc)
        return ctx


class MaterialCreateView(SoloPropietarioMixin, View):
    '''/<username>/materiales/agregar/ : alta de un material en el microservicio.'''

    template_name = 'inventario/material_form.html'

    def get(self, request, username):
        return self._pintar(data=None)

    def post(self, request, username):
        return self._pintar(data=request.POST)

    def _pintar(self, data):
        ctx = {'propietario': self.request.user}
        try:
            # Las opciones de los desplegables vienen de la API: sin ella no hay form.
            form, formset = formularios_material(data)
        except services.MicroserviceError as exc:
            ctx['error'] = str(exc)
            return render(self.request, self.template_name, ctx, status=503)

        if data is not None and form.is_valid() and formset.is_valid():
            try:
                services.create_item(
                    created_by=self.request.user.username, **payload_material(form, formset)
                )
            except services.MicroserviceError as exc:
                errores_api_en_form(form, exc)
            else:
                return redirect('materiales', username=self.request.user.username)

        ctx.update(form=form, formset=formset)
        return render(self.request, self.template_name, ctx)
