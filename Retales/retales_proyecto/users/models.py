from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Campos de usuario"""

    email = models.EmailField("correo electrónico", unique=True)

    def __str__(self):
        return self.username