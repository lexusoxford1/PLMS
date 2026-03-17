from django.contrib import admin

from .models import Badge, UserBadge


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("name", "criteria_key", "course", "award_type", "xp_reward", "is_active", "created_at")
    list_filter = ("award_type", "is_active")
    search_fields = ("name", "criteria_key", "description", "course__title")


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "course", "is_seen", "awarded_at")
    list_filter = ("course", "badge__award_type", "is_seen")
    search_fields = ("user__username", "badge__name", "course__title")
