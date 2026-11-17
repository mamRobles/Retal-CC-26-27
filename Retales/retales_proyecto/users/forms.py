from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User

# Rutas de primer nivel en config/urls.py: un usuario con ese nombre "taparía" la ruta
# (o al revés), porque /<username>/ va al final y lo captura todo.
RESERVADOS = {"admin", "buscar", "cuenta", "registro", "health", "panel", "static", "__reload__"}

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields  = ("username", "email", "password1", "password2")
    def clean_username(self):
        username = self.cleaned_data["username"]
        if username.lower() in RESERVADOS:
            raise forms.ValidationError("Este nombre de usuario no está disponible.")
        return username

