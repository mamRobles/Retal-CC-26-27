from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import models
from django.urls import reverse


class Proyecto(models.Model):
    """Un proyecto de artesanía textil de un usuario (HU2)."""

    class Estado(models.TextChoices):
        PLANEADO = 'planeado', 'Planeado'
        EN_CURSO = 'en_curso', 'En curso'
        TERMINADO = 'terminado', 'Terminado'

    class Tecnica(models.TextChoices):
        PUNTO = 'punto', 'Punto'
        GANCHILLO = 'ganchillo', 'Ganchillo'
        BORDADO = 'bordado', 'Bordado'
        COSTURA = 'costura', 'Costura'
        OTRA = 'otra', 'Otra'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='proyectos'
    )
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    tecnica = models.CharField(max_length=30, choices=Tecnica.choices, default=Tecnica.PUNTO)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PLANEADO)
    progreso = models.PositiveSmallIntegerField(
        default=0, validators=[MaxValueValidator(100)]
    )  # 0–100 %
    notas = models.TextField(blank=True)
    opinion = models.TextField(blank=True)  # al terminar
    publico = models.BooleanField(default=False)  # visible en el buscador (HU3)
    materiales_ids = models.JSONField(default=list, blank=True)  # ids del microservicio
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-actualizado',)

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse(
            'proyecto_detalle', kwargs={'username': self.usuario.username, 'pk': self.pk}
        )
