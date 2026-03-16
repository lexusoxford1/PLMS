from django.contrib import admin

from .models import Choice, Question, Quiz, QuizAttempt


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "passing_score", "max_attempts", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "lesson__title", "lesson__course__title")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("prompt", "quiz", "question_type", "order", "points")
    list_filter = ("question_type",)
    search_fields = ("prompt", "quiz__title")
    ordering = ("quiz", "order")


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ("text", "question", "is_correct", "order")
    list_filter = ("is_correct",)
    search_fields = ("text", "question__prompt")
    ordering = ("question", "order")


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "quiz", "score", "passed", "attempted_at")
    list_filter = ("passed", "quiz")
    search_fields = ("user__username", "quiz__title")
