from typing import ClassVar

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


class CustomUserAdmin(UserAdmin):
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )
    model = User
    list_display: ClassVar[list[str]]  = [
        "email",
        "username",
        "is_staff",
        "is_active",
    ]
    search_fields: ClassVar[list[str]]  = ['username','email']


admin.site.register(User, CustomUserAdmin)