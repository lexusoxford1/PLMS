from django.db import models
from django.template.defaultfilters import slugify


def generate_badge_slug(value, *, pk=None):
    base_slug = slugify(value)[:200] or "badge"
    candidate = base_slug
    counter = 2
    while Badge.objects.exclude(pk=pk).filter(slug=candidate).exists():
        suffix = f"-{counter}"
        candidate = f"{base_slug[: max(1, 200 - len(suffix))]}{suffix}"
        counter += 1
    return candidate


class Badge(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to="badges/", blank=True, null=True)
    course = models.OneToOneField(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="completion_badge",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_badge_slug(self.name, pk=self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="user_badges")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="awards")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="badge_awards")
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-awarded_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "badge"], name="unique_user_badge"),
        ]

    def __str__(self):
        return f"{self.user} earned {self.badge}"
