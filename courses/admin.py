from django.contrib import admin

from .models import Course, Enrollment, LearningMaterial, Lesson


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    ordering = ("order",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "difficulty", "estimated_hours", "is_published", "created_by")
    list_filter = ("category", "difficulty", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "description")
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "activity_validator", "activity_language", "is_published")
    list_filter = ("course", "is_published")
    search_fields = ("title", "summary", "lecture_content")
    ordering = ("course", "order")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "enrolled_at", "completed_at")
    list_filter = ("course",)
    search_fields = ("user__username", "course__title")


@admin.register(LearningMaterial)
class LearningMaterialAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "order", "material_type", "source_type", "presentation_provider", "uploaded_at")
    list_filter = ("material_type", "source_type", "presentation_provider", "lesson__course")
    search_fields = ("title", "description", "lesson__title", "lesson__course__title", "external_url")
