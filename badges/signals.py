from django.db.models.signals import post_save
from django.dispatch import receiver

from courses.models import Course, Enrollment

from .services import award_enrollment_badge, ensure_course_badges, ensure_platform_badges, sync_platform_badges


@receiver(post_save, sender=Course)
def sync_course_badges(sender, instance, **kwargs):
    ensure_course_badges(instance)
    ensure_platform_badges()


@receiver(post_save, sender=Enrollment)
def award_enrollment_badge_on_create(sender, instance, created, **kwargs):
    if created:
        award_enrollment_badge(instance.user, instance.course)
        sync_platform_badges(instance.user)
