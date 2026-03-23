from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    LEARNER = "learner"
    ADMIN = "admin"
    MANUAL = "manual"
    GOOGLE = "google"
    FACEBOOK = "facebook"
    GITHUB = "github"

    ROLE_CHOICES = (
        (LEARNER, "Learner"),
        (ADMIN, "Admin"),
    )
    PROVIDER_CHOICES = (
        (MANUAL, "Manual"),
        (GOOGLE, "Google"),
        (FACEBOOK, "Facebook"),
        (GITHUB, "GitHub"),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=LEARNER)
    auth_provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default=MANUAL)
    title = models.CharField(max_length=120, blank=True)
    phone_number = models.CharField(max_length=40, blank=True)
    organization = models.CharField(max_length=160, blank=True)
    certificate_name = models.CharField(max_length=200, blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    bio = models.TextField(blank=True)
    last_seen_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.is_staff:
            self.role = self.ADMIN
        super().save(*args, **kwargs)

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    @property
    def initials(self):
        letters = [value[:1].upper() for value in [self.first_name, self.last_name] if value]
        if letters:
            return "".join(letters[:2])
        return (self.username[:2] or "PL").upper()

    @property
    def profile_title(self):
        return self.title or self.get_role_display()

    def get_certificate_display_name(self):
        return self.certificate_name.strip() or self.display_name

    def get_certificate_identity_line(self):
        items = [self.title.strip(), self.organization.strip()]
        return " | ".join(item for item in items if item)

    def __str__(self):
        return self.display_name
