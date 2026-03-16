from django.contrib import admin

from .models import Badge, UserBadge


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description", "course__title")


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "course", "awarded_at")
    list_filter = ("course",)
    search_fields = ("user__username", "badge__name", "course__title")
