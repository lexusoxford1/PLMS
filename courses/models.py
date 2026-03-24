from pathlib import Path

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
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
    CATEGORY_CSHARP = "csharp"
    CATEGORY_PYTHON = "python"
    CATEGORY_PHP = "php"
    CATEGORY_GENERAL = "general"

    CATEGORY_CHOICES = (
        (CATEGORY_CSHARP, "C# and .NET Development"),
        (CATEGORY_PYTHON, "Python Programming and Automation"),
        (CATEGORY_PHP, "PHP Web Development"),
        (CATEGORY_GENERAL, "General Programming Foundations"),
    )

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
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default=CATEGORY_GENERAL)
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
    ACTIVITY_VALIDATOR_PATTERN = "pattern"
    ACTIVITY_VALIDATOR_CODE = "code_runner"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    order = models.PositiveIntegerField(default=1)
    summary = models.TextField(blank=True)
    image = models.ImageField(upload_to="lesson_images/", blank=True, null=True)
    lecture_content = models.TextField()
    activity_title = models.CharField(max_length=200, blank=True)
    activity_instructions = models.TextField(blank=True)
    activity_hint = models.TextField(blank=True)
    activity_validation_rules = models.JSONField(default=dict, blank=True)
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
    def has_activity_validation(self):
        return bool(self.activity_validation_rules)

    @property
    def activity_validator(self):
        rules = self.activity_validation_rules or {}
        if rules.get("validator") == self.ACTIVITY_VALIDATOR_CODE or rules.get("language"):
            return self.ACTIVITY_VALIDATOR_CODE
        return self.ACTIVITY_VALIDATOR_PATTERN

    @property
    def activity_language(self):
        return (self.activity_validation_rules or {}).get("language", "")

    @property
    def uses_code_runner(self):
        return self.activity_validator == self.ACTIVITY_VALIDATOR_CODE

    @property
    def has_quiz(self):
        try:
            return self.quiz is not None
        except ObjectDoesNotExist:
            return False

    def __str__(self):
        return f"{self.course.title} - Lesson {self.order}: {self.title}"


class LearningMaterial(models.Model):
    MATERIAL_DOCUMENT = "document"
    MATERIAL_IMAGE = "image"
    MATERIAL_ARCHIVE = "archive"
    MATERIAL_PRESENTATION = "presentation"
    MATERIAL_OTHER = "other"

    MATERIAL_TYPE_CHOICES = (
        (MATERIAL_DOCUMENT, "Document"),
        (MATERIAL_IMAGE, "Image"),
        (MATERIAL_ARCHIVE, "Archive"),
        (MATERIAL_PRESENTATION, "Presentation"),
        (MATERIAL_OTHER, "Other"),
    )

    SOURCE_FILE = "file"
    SOURCE_URL = "url"

    SOURCE_TYPE_CHOICES = (
        (SOURCE_FILE, "Uploaded file"),
        (SOURCE_URL, "External link"),
    )

    PRESENTATION_PROVIDER_NONE = "none"
    PRESENTATION_PROVIDER_UPLOAD = "upload"
    PRESENTATION_PROVIDER_GOOGLE_SLIDES = "google_slides"
    PRESENTATION_PROVIDER_CANVA = "canva"
    PRESENTATION_PROVIDER_EMBED = "embed"

    PRESENTATION_PROVIDER_CHOICES = (
        (PRESENTATION_PROVIDER_NONE, "Not a presentation"),
        (PRESENTATION_PROVIDER_UPLOAD, "Uploaded deck"),
        (PRESENTATION_PROVIDER_GOOGLE_SLIDES, "Google Slides"),
        (PRESENTATION_PROVIDER_CANVA, "Canva"),
        (PRESENTATION_PROVIDER_EMBED, "Direct embed link"),
    )

    PRESENTATION_UPLOAD_EXTENSIONS = {".ppt", ".pptx", ".pdf"}

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="materials")
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="lesson_materials/", blank=True, null=True)
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPE_CHOICES, default=MATERIAL_DOCUMENT)
    source_type = models.CharField(max_length=12, choices=SOURCE_TYPE_CHOICES, default=SOURCE_FILE)
    external_url = models.URLField(blank=True)
    presentation_provider = models.CharField(
        max_length=20,
        choices=PRESENTATION_PROVIDER_CHOICES,
        default=PRESENTATION_PROVIDER_NONE,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["lesson__course", "lesson__order", "order", "title"]

    def clean(self):
        errors = {}
        is_presentation = self.material_type == self.MATERIAL_PRESENTATION
        has_file = bool(self.file)
        has_external_url = bool((self.external_url or "").strip())
        file_extension = self.file_extension

        if self.source_type == self.SOURCE_FILE and not has_file:
            errors.setdefault("file", []).append("Upload a file for this attachment.")

        if self.source_type == self.SOURCE_URL:
            if not is_presentation:
                errors.setdefault("source_type", []).append(
                    "External links are only supported for presentation materials."
                )
            if not has_external_url:
                errors.setdefault("external_url", []).append("Paste a presentation link.")

        if self.source_type == self.SOURCE_FILE and has_external_url:
            self.external_url = ""

        if is_presentation:
            if self.source_type == self.SOURCE_FILE:
                if self.presentation_provider not in {
                    self.PRESENTATION_PROVIDER_NONE,
                    self.PRESENTATION_PROVIDER_UPLOAD,
                }:
                    errors.setdefault("presentation_provider", []).append(
                        "Uploaded presentation files must use the uploaded deck provider."
                    )
                if has_file and file_extension not in self.PRESENTATION_UPLOAD_EXTENSIONS:
                    allowed = ", ".join(sorted(self.PRESENTATION_UPLOAD_EXTENSIONS))
                    errors.setdefault("file", []).append(
                        f"Upload a supported presentation deck ({allowed})."
                    )
            elif self.presentation_provider not in {
                self.PRESENTATION_PROVIDER_GOOGLE_SLIDES,
                self.PRESENTATION_PROVIDER_CANVA,
                self.PRESENTATION_PROVIDER_EMBED,
            }:
                errors.setdefault("presentation_provider", []).append(
                    "Choose how this presentation link should be embedded."
                )
        else:
            if self.source_type != self.SOURCE_FILE:
                errors.setdefault("source_type", []).append(
                    "Documents, images, archives, and other files must be uploaded."
                )
            if self.presentation_provider not in {
                self.PRESENTATION_PROVIDER_NONE,
                self.PRESENTATION_PROVIDER_UPLOAD,
            }:
                errors.setdefault("presentation_provider", []).append(
                    "Only presentation materials can use Canva, Google Slides, or embed providers."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.lesson} - {self.title}"

    def save(self, *args, **kwargs):
        if self.material_type == self.MATERIAL_PRESENTATION:
            if self.source_type == self.SOURCE_FILE:
                self.presentation_provider = self.PRESENTATION_PROVIDER_UPLOAD
                self.external_url = ""
            else:
                self.file = None
                if self.presentation_provider == self.PRESENTATION_PROVIDER_NONE:
                    self.presentation_provider = self.PRESENTATION_PROVIDER_EMBED
        else:
            self.source_type = self.SOURCE_FILE
            self.presentation_provider = self.PRESENTATION_PROVIDER_NONE
            self.external_url = ""
        super().save(*args, **kwargs)

    @property
    def file_extension(self):
        if not self.file:
            return ""
        return Path(self.file.name).suffix.lower()

    @property
    def file_name(self):
        if not self.file:
            return ""
        return Path(self.file.name).name

    @property
    def is_presentation(self):
        return self.material_type == self.MATERIAL_PRESENTATION

    @property
    def source_url(self):
        if self.source_type == self.SOURCE_URL:
            return (self.external_url or "").strip()
        if not self.file:
            return ""
        try:
            return self.file.url
        except ValueError:
            return ""


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
