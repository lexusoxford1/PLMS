from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "title",
        "role",
        "auth_provider",
        "is_staff",
    )
    list_filter = ("role", "auth_provider", "is_staff", "is_superuser", "is_active")
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "PLMS Details",
            {
                "fields": (
                    "role",
                    "auth_provider",
                    "title",
                    "organization",
                    "phone_number",
                    "certificate_name",
                    "profile_picture",
                    "bio",
                )
            },
        ),
    )
