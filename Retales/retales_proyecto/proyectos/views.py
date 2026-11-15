from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import ProyectoForm
from .models import Proyecto


class PropietarioMixin:
    """Busca al usuario de la URL (/<username>/proyectos/...) y decide qué puede ver.

    - El dueño ve todos sus proyectos.
    - Cualquier otro (o un anónimo) solo ve los marcados como públicos.
    """

    def dispatch(self, request, *args, **kwargs):
        self.propietario = get_object_or_404(get_user_model(), username=kwargs['username'])
        return super().dispatch(request, *args, **kwargs)

    def es_propietario(self):
        return self.request.user == self.propietario

    def get_queryset(self):
        qs = Proyecto.objects.filter(usuario=self.propietario)
        return qs if self.es_propietario() else qs.filter(publico=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['propietario'] = self.propietario
        ctx['es_propietario'] = self.es_propietario()
        return ctx


class SoloPropietarioMixin(LoginRequiredMixin, PropietarioMixin):
    """Para crear/editar/borrar: hay que estar logueado y ser el dueño.
    Si no lo eres, devolvemos 404 (no revelamos que el proyecto existe)."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.username != kwargs['username']:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('proyecto_list', kwargs={'username': self.propietario.username})


class ProyectoListView(PropietarioMixin, ListView):
    template_name = 'proyectos/proyecto_list.html'
    context_object_name = 'proyectos'


class ProyectoDetailView(PropietarioMixin, DetailView):
    template_name = 'proyectos/proyecto_detail.html'
    context_object_name = 'proyecto'


class ProyectoCreateView(SoloPropietarioMixin, CreateView):
    form_class = ProyectoForm
    template_name = 'proyectos/proyecto_form.html'

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)


class ProyectoUpdateView(SoloPropietarioMixin, UpdateView):
    form_class = ProyectoForm
    template_name = 'proyectos/proyecto_form.html'
    context_object_name = 'proyecto'


class ProyectoDeleteView(SoloPropietarioMixin, DeleteView):
    template_name = 'proyectos/proyecto_confirm_delete.html'
    context_object_name = 'proyecto'


class BusquedaView(ListView):
    """Buscador global (HU3): solo proyectos públicos, por título, descripción o técnica."""

    template_name = 'proyectos/busqueda.html'
    context_object_name = 'proyectos'
    paginate_by = 20

    def get_queryset(self):
        qs = Proyecto.objects.filter(publico=True).select_related('usuario')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(titulo__icontains=q) | Q(descripcion__icontains=q) | Q(tecnica__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        return ctx
