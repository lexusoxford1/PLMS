import os
import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.db import models
from django.utils import timezone

from .generator import generate_certificate_pdf


class Certificate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="certificates")
    badge = models.ForeignKey(
        "badges.Badge",
        on_delete=models.SET_NULL,
        related_name="certificates",
        null=True,
        blank=True,
    )
    certificate_number = models.CharField(max_length=32, unique=True, blank=True)
    file = models.FileField(upload_to="certificates/", blank=True)
    issued_at = models.DateTimeField(blank=True, null=True)
    emailed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "course"], name="unique_certificate_per_course"),
        ]

    def save(self, *args, **kwargs):
        if not self.certificate_number:
            self.certificate_number = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    def _render_file(self, issued_at):
        if not self.certificate_number:
            self.certificate_number = uuid.uuid4().hex[:12].upper()
        pdf_bytes = generate_certificate_pdf(self, issued_at=issued_at)
        filename = f"{self.course.slug}-{self.user.username}-{self.certificate_number}.pdf"
        upload_name = self.file.field.generate_filename(self, filename)
        if self.file.name and self.file.name != upload_name:
            self.file.storage.delete(self.file.name)
        self.file.storage.delete(upload_name)
        self.file.save(filename, ContentFile(pdf_bytes), save=False)

    def refresh_artifact(self):
        issued_at = self.issued_at or timezone.now()
        self._render_file(issued_at)
        self.issued_at = issued_at
        self.save()

    def issue(self, send_email=True):
        issued_at = self.issued_at or timezone.now()
        self._render_file(issued_at)
        self.issued_at = issued_at
        self.save()
        if send_email:
            self.send_via_email()

    def send_via_email(self):
        if not self.user.email or not self.file:
            return False

        self.file.open("rb")
        email = EmailMessage(
            subject=f"Your PLMS certificate for {self.course.title}",
            body=(
                f"Congratulations, {self.user.get_certificate_display_name()}!\n\n"
                f"Attached is your certificate for completing {self.course.title}."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[self.user.email],
        )
        email.attach(
            os.path.basename(self.file.name),
            self.file.read(),
            "application/pdf",
        )
        sent_count = email.send(fail_silently=True)
        self.file.close()
        if sent_count:
            self.emailed_at = timezone.now()
            self.save(update_fields=["emailed_at"])
        return bool(sent_count)

    def __str__(self):
        return f"Certificate for {self.user} - {self.course}"
