from django.db import transaction
from django.utils import timezone

from .permissions import can_access_learner_features


def get_or_create_lesson_progress(user, lesson):
    from progress.models import LessonProgress

    defaults = {
        "activity_completed": not lesson.has_activity,
        "quiz_passed": not lesson.has_quiz,
    }
    progress, _ = LessonProgress.objects.get_or_create(user=user, lesson=lesson, defaults=defaults)
    changed = False

    if not lesson.has_activity and not progress.activity_completed:
        progress.activity_completed = True
        changed = True
    if not lesson.has_quiz and not progress.quiz_passed:
        progress.quiz_passed = True
        changed = True

    if changed:
        progress.refresh_completion_state()
        progress.save()

    return progress


def can_access_lesson(user, lesson):
    from courses.models import Enrollment
    from progress.models import LessonProgress

    if not can_access_learner_features(user):
        return False
    if not Enrollment.objects.filter(user=user, course=lesson.course).exists():
        return False

    previous_lesson = (
        lesson.course.lessons.filter(is_published=True, order__lt=lesson.order).order_by("-order").first()
    )
    if previous_lesson is None:
        return True

    return LessonProgress.objects.filter(
        user=user,
        lesson=previous_lesson,
        completed_at__isnull=False,
    ).exists()


def course_completion_percentage(user, course):
    if not can_access_learner_features(user):
        return 0

    lesson_ids = list(course.lessons.filter(is_published=True).values_list("id", flat=True))
    if not lesson_ids:
        return 0

    from progress.models import LessonProgress

    completed_count = LessonProgress.objects.filter(
        user=user,
        lesson_id__in=lesson_ids,
        completed_at__isnull=False,
    ).count()
    return int((completed_count / len(lesson_ids)) * 100)


def build_course_outline(user, course):
    progress_map = {}
    if can_access_learner_features(user):
        from progress.models import LessonProgress

        progress_map = {
            progress.lesson_id: progress
            for progress in LessonProgress.objects.filter(user=user, lesson__course=course).select_related("lesson")
        }

    outline = []
    for lesson in course.lessons.filter(is_published=True).order_by("order"):
        outline.append(
            {
                "lesson": lesson,
                "progress": progress_map.get(lesson.id),
                "accessible": can_access_lesson(user, lesson) if can_access_learner_features(user) else False,
            }
        )
    return outline


@transaction.atomic
def award_course_completion(user, course):
    from badges.services import award_completion_badge, award_enrollment_badge, sync_platform_badges
    from certificates.models import Certificate
    from courses.models import Enrollment
    from progress.models import LessonProgress

    if not can_access_learner_features(user):
        return None

    lesson_ids = list(course.lessons.filter(is_published=True).values_list("id", flat=True))
    if not lesson_ids:
        return None

    completed_ids = set(
        LessonProgress.objects.filter(
            user=user,
            lesson_id__in=lesson_ids,
            completed_at__isnull=False,
        ).values_list("lesson_id", flat=True)
    )
    if set(lesson_ids) - completed_ids:
        return None

    enrollment = Enrollment.objects.filter(user=user, course=course).first()
    if enrollment and enrollment.completed_at is None:
        enrollment.completed_at = timezone.now()
        enrollment.save(update_fields=["completed_at"])

    award_enrollment_badge(user, course)
    user_badge, _ = award_completion_badge(user, course)
    badge = user_badge.badge

    certificate, created = Certificate.objects.get_or_create(
        user=user,
        course=course,
        defaults={"badge": badge},
    )
    if certificate.badge_id != badge.id:
        certificate.badge = badge
        certificate.save(update_fields=["badge"])

    if created or not certificate.file:
        certificate.issue()

    sync_platform_badges(user)
    return certificate


def sync_progress_after_quiz_attempt(attempt):
    from badges.services import sync_platform_badges

    if not can_access_learner_features(attempt.user):
        return None

    progress = get_or_create_lesson_progress(attempt.user, attempt.quiz.lesson)
    if attempt.passed and not progress.quiz_passed:
        progress.quiz_passed = True
    progress.refresh_completion_state()
    progress.save()

    if attempt.passed:
        sync_platform_badges(attempt.user)

    if progress.completed_at is not None:
        award_course_completion(attempt.user, attempt.quiz.lesson.course)

    return progress
