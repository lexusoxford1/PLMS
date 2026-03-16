from django.db.models.signals import post_save
from django.dispatch import receiver

from quizzes.models import QuizAttempt

from .utils import sync_progress_after_quiz_attempt


@receiver(post_save, sender=QuizAttempt)
def update_progress_after_quiz_attempt(sender, instance, created, **kwargs):
    if created:
        sync_progress_after_quiz_attempt(instance)
