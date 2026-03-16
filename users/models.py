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
    bio = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if self.is_staff:
            self.role = self.ADMIN
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_full_name() or self.username
