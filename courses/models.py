from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.template.defaultfilters import slugify


def generate_unique_slug(model_cls, value, *, pk=None, queryset=None):
    base_slug = slugify(value)[:200] or "item"
    candidate = base_slug
    counter = 2
    scope = queryset if queryset is not None else model_cls.objects.all()
    while scope.exclude(pk=pk).filter(slug=candidate).exists():
        suffix = f"-{counter}"
        candidate = f"{base_slug[: max(1, 200 - len(suffix))]}{suffix}"
        counter += 1
    return candidate


class Course(models.Model):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

    DIFFICULTY_CHOICES = (
        (BEGINNER, "Beginner"),
        (INTERMEDIATE, "Intermediate"),
        (ADVANCED, "Advanced"),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    overview = models.TextField(blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default=BEGINNER)
    estimated_hours = models.PositiveIntegerField(default=1)
    image = models.ImageField(upload_to="course_materials/", blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_courses",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Course, self.title, pk=self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    order = models.PositiveIntegerField(default=1)
    summary = models.TextField(blank=True)
    lecture_content = models.TextField()
    activity_title = models.CharField(max_length=200, blank=True)
    activity_instructions = models.TextField(blank=True)
    activity_hint = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["course", "order"]
        constraints = [
            models.UniqueConstraint(fields=["course", "order"], name="unique_lesson_order_per_course"),
            models.UniqueConstraint(fields=["course", "slug"], name="unique_lesson_slug_per_course"),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(
                Lesson,
                self.title,
                pk=self.pk,
                queryset=Lesson.objects.filter(course=self.course),
            )
        super().save(*args, **kwargs)

    @property
    def has_activity(self):
        return bool(self.activity_instructions.strip())

    @property
    def has_quiz(self):
        try:
            return self.quiz is not None
        except ObjectDoesNotExist:
            return False

    def __str__(self):
        return f"{self.course.title} - Lesson {self.order}: {self.title}"


class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-enrolled_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "course"], name="unique_course_enrollment"),
        ]

    def __str__(self):
        return f"{self.user} enrolled in {self.course}"
