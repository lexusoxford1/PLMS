from django.contrib import admin

from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "certificate_number", "issued_at", "emailed_at")
    list_filter = ("course",)
    search_fields = ("user__username", "course__title", "certificate_number")
