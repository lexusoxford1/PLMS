from django.conf import settings
from django.db import models
from django.utils import timezone


class LessonProgress(models.Model):
    PENDING = "pending"
    CORRECT = "correct"
    INCORRECT = "incorrect"
    ACTIVITY_STATUS_CHOICES = (
        (PENDING, "Pending"),
        (CORRECT, "Correct"),
        (INCORRECT, "Incorrect"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey("courses.Lesson", on_delete=models.CASCADE, related_name="progress_records")
    lecture_completed = models.BooleanField(default=False)
    activity_completed = models.BooleanField(default=False)
    activity_response = models.TextField(blank=True)
    activity_attempts = models.PositiveIntegerField(default=0)
    activity_status = models.CharField(max_length=20, choices=ACTIVITY_STATUS_CHOICES, default=PENDING)
    activity_feedback_title = models.CharField(max_length=255, blank=True)
    activity_feedback_body = models.TextField(blank=True)
    activity_result_data = models.JSONField(default=dict, blank=True)
    activity_last_submitted_at = models.DateTimeField(blank=True, null=True)
    quiz_passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["lesson__course", "lesson__order"]
        constraints = [
            models.UniqueConstraint(fields=["user", "lesson"], name="unique_lesson_progress"),
        ]

    @property
    def is_complete(self):
        return self.lecture_completed and self.activity_completed and self.quiz_passed

    def refresh_completion_state(self):
        if not self.lesson.has_activity:
            self.activity_completed = True
        if not self.lesson.has_quiz:
            self.quiz_passed = True

        if self.is_complete and self.completed_at is None:
            self.completed_at = timezone.now()
        elif not self.is_complete:
            self.completed_at = None

    def save(self, *args, **kwargs):
        self.refresh_completion_state()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.lesson}"
