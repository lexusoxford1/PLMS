from django.contrib import admin

from .models import LessonProgress


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "lesson",
        "lecture_completed",
        "activity_completed",
        "activity_status",
        "activity_attempts",
        "activity_last_submitted_at",
        "quiz_passed",
        "completed_at",
    )
    list_filter = ("lecture_completed", "activity_completed", "activity_status", "quiz_passed")
    search_fields = ("user__username", "lesson__title", "lesson__course__title")
