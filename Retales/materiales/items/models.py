from django.db import models


class Item(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    creado_por = models.CharField(max_length=150)
    creado_a = models.DateTimeField(auto_now_add=True)
    grosor_lana = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-creado_a']

    def __str__(self):
        return self.titulo
