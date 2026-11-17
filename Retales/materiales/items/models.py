from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# Composicion de la lana (acrilico 100% por ejemplo)
class Composicion(models.Model):
    class Fibra(models.TextChoices):
        ACRILICO = "acrilico", "Acrílico"
        ALGODON = "algodon", "Algodón"
        CACHEMIRA = "cachemira", "Cachemira"
        LANA = "lana", "Lana"
        MERINO = "merino", "Merino"
        NYLON = "nylon", "Nylon"
        POLIESTER = "poliester", "Poliéster"
        SEDA = "seda", "Seda"

    item = models.ForeignKey("Item", on_delete=models.CASCADE, related_name="composicion")
    fibra = models.CharField(max_length=20, choices=Fibra.choices)
    porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01")), MaxValueValidator(Decimal(100))],
    )

    class Meta:
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(fields=["item", "fibra"], name="fibra_unica_por_item"),
        ]


class Item(models.Model):
    class TamLana(models.TextChoices):
        THREAD = "thread", "Thread (CYC 0)"
        COBWEB = "cobweb", "Cobweb (CYC 0)"
        LACE = "lace", "Lace (CYC 0)"
        LIGHT_FINGERING = "light_fingering", "Light Fingering (CYC 0)"
        FINGERING = "fingering", "Fingering (CYC 1)"
        SPORT = "sport", "Sport (CYC 2)"
        DK = "dk", "DK (CYC 3)"
        WORSTED = "worsted", "Worsted (CYC 4)"
        ARAN = "aran", "Aran (CYC 4)"
        BULKY = "bulky", "Bulky (CYC 5)"
        SUPER_BULKY = "super_bulky", "Super Bulky (CYC 6)"
        JUMBO = "jumbo", "Jumbo (CYC 7)"

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    creado_por = models.CharField(max_length=150)
    creado_a = models.DateTimeField(auto_now_add=True)
    tam_lana = models.CharField(max_length=20, choices=TamLana.choices, default=TamLana.SPORT)
    tam_aguja_mm = models.DecimalField(null=True, blank=True,
        max_digits=4, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.1")), MaxValueValidator(Decimal(20))],
    )
    tam_ganchillo_mm = models.DecimalField(null=True, blank=True,
        max_digits=4, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.1")), MaxValueValidator(Decimal(20))],
    )
    marca = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-creado_a']  # noqa: RUF012 (cambiarlo a tupla generaría una migración)

    def __str__(self):
        return self.titulo