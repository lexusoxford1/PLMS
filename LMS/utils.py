from django.db import transaction
from django.utils import timezone


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

    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_staff or getattr(user, "role", "") == "admin":
        return True
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
    if not getattr(user, "is_authenticated", False):
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
    if getattr(user, "is_authenticated", False):
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
                "accessible": can_access_lesson(user, lesson) if getattr(user, "is_authenticated", False) else False,
            }
        )
    return outline


@transaction.atomic
def award_course_completion(user, course):
    from badges.models import Badge, UserBadge
    from certificates.models import Certificate
    from courses.models import Enrollment
    from progress.models import LessonProgress

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

    badge, _ = Badge.objects.get_or_create(
        course=course,
        defaults={
            "name": f"{course.title} Completion Badge",
            "description": f"Awarded for successfully finishing {course.title}.",
        },
    )
    user_badge, created = UserBadge.objects.get_or_create(
        user=user,
        badge=badge,
        defaults={"course": course},
    )
    if not created and user_badge.course_id != course.id:
        user_badge.course = course
        user_badge.save(update_fields=["course"])

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

    return certificate


def sync_progress_after_quiz_attempt(attempt):
    progress = get_or_create_lesson_progress(attempt.user, attempt.quiz.lesson)
    if attempt.passed and not progress.quiz_passed:
        progress.quiz_passed = True
    progress.refresh_completion_state()
    progress.save()

    if progress.completed_at is not None:
        award_course_completion(attempt.user, attempt.quiz.lesson.course)

    return progress
