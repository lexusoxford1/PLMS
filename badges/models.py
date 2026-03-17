from django.db import models
from django.db.models import Q
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
    ENROLLMENT = "enrollment"
    COMPLETION = "completion"
    MILESTONE = "milestone"
    AWARD_TYPE_CHOICES = (
        (ENROLLMENT, "Enrollment"),
        (COMPLETION, "Completion"),
        (MILESTONE, "Milestone"),
    )

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    criteria_key = models.CharField(max_length=160, unique=True, blank=True, null=True)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to="badges/", blank=True, null=True)
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="badges",
        null=True,
        blank=True,
    )
    award_type = models.CharField(max_length=20, choices=AWARD_TYPE_CHOICES, default=COMPLETION)
    xp_reward = models.PositiveIntegerField(default=40)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["course__title", "award_type", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "award_type"],
                condition=Q(course__isnull=False),
                name="unique_badge_per_course_and_type",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_badge_slug(self.name, pk=self.pk)
        super().save(*args, **kwargs)

    @property
    def visual_spec(self):
        from .catalog import get_badge_visual_spec

        return get_badge_visual_spec(self)

    @property
    def stage_label(self):
        return self.visual_spec.get("stage_label") or self.get_award_type_display()

    @property
    def is_completion_badge(self):
        return self.award_type == self.COMPLETION

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="user_badges")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="awards")
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="badge_awards",
        null=True,
        blank=True,
    )
    is_seen = models.BooleanField(default=True)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-awarded_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "badge"], name="unique_user_badge"),
        ]

    def __str__(self):
        return f"{self.user} earned {self.badge}"
