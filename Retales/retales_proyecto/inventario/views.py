from core import services
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView

from .forms import errores_api_en_form, formularios_material, payload_material


class SoloPropietarioMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.username != kwargs['username']:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

class MaterialPropioMixin:
     def _material_propio(self, item_id):
        try:
            material = services.get_item(item_id)
        except services.MaterialNoEncontrado as exc:
            raise Http404 from exc
        if material['created_by'] != self.request.user.username:
            raise Http404
        return material
class MaterialListView(TemplateView):
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
    template_name = 'inventario/material_form.html'

    def get(self, request, username):
        return self._pintar(data=None)

    def post(self, request, username):
        return self._pintar(data=request.POST)

    def _pintar(self, data):
        ctx = {'propietario': self.request.user, 'titulo': 'Nuevo Material'}
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


class MaterialDeleteView(MaterialPropioMixin, SoloPropietarioMixin, View):
    template_name = 'inventario/material_confirm_delete.html'

    def get(self, request, username, item_id):
        try:
            material = self._material_propio(item_id)
        except services.MicroserviceError as exc:
            return self._sin_servicio(exc)
        return render(request, self.template_name, {'material': material})

    def post(self, request, username, item_id):
        try:
            # Se vuelve a comprobar el dueño: el POST puede llegar sin pasar por el GET.
            self._material_propio(item_id)
            services.delete_item(item_id)
        except services.MicroserviceError as exc:
            return self._sin_servicio(exc)
        self._desenlazar_de_proyectos(item_id)
        return redirect('materiales', username=username)

   

    def _desenlazar_de_proyectos(self, item_id):
        '''Quita el id borrado de los proyectos del usuario que lo tuvieran enlazado.'''
        for proyecto in self.request.user.proyectos.all():
            if item_id in proyecto.materiales_ids:
                proyecto.materiales_ids = [i for i in proyecto.materiales_ids if i != item_id]
                proyecto.save(update_fields=['materiales_ids'])

    def _sin_servicio(self, exc):
        return render(self.request, self.template_name, {'error': str(exc)}, status=503)
class MaterialUpdateView(SoloPropietarioMixin, MaterialPropioMixin, View):
    '''/<username>/materiales/<id>/editar/ : edita un material en el microservicio.'''

    template_name = 'inventario/material_form.html'

    def get(self, request, username, item_id):
        return self._pintar(item_id, data=None)

    def post(self, request, username, item_id):
        return self._pintar(item_id, data=request.POST)

    def _pintar(self, item_id, data):
        ctx = {'propietario': self.request.user}
        try:
            # En el POST también se comprueba el dueño: puede llegar sin pasar por el GET.
            material = self._material_propio(item_id)
            form, formset = formularios_material(data, item=material)
        except services.MicroserviceError as exc:
            ctx['error'] = str(exc)
            return render(self.request, self.template_name, ctx, status=503)

        ctx['titulo'] = f'Editar «{material["title"]}»'
        if data is not None and form.is_valid() and formset.is_valid():
            try:
                services.update_item(item_id, **payload_material(form, formset))
            except services.MicroserviceError as exc:
                errores_api_en_form(form, exc)
            else:
                return redirect('materiales', username=self.request.user.username)

        ctx.update(form=form, formset=formset)
        return render(self.request, self.template_name, ctx)