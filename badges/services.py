from collections import defaultdict
from decimal import Decimal

from django.db import transaction

from LMS.permissions import is_admin_account

from .catalog import get_badge_defaults, get_platform_badge_definitions
from .models import Badge, UserBadge


BADGE_TYPE_ORDER = {
    Badge.ENROLLMENT: 0,
    Badge.COMPLETION: 1,
    Badge.MILESTONE: 2,
}

BADGE_STATUS_ORDER = {
    "earned": 0,
    "in_progress": 1,
    "locked": 2,
}


def ensure_badge(*, course=None, award_type=None, criteria_key=None):
    defaults = get_badge_defaults(course=course, award_type=award_type, criteria_key=criteria_key)
    badge, _ = Badge.objects.update_or_create(
        criteria_key=defaults["criteria_key"],
        defaults={
            **defaults,
            "course": course,
            "award_type": award_type or Badge.MILESTONE,
        },
    )
    return badge


def ensure_course_badges(course):
    return {
        Badge.ENROLLMENT: ensure_badge(course=course, award_type=Badge.ENROLLMENT),
        Badge.COMPLETION: ensure_badge(course=course, award_type=Badge.COMPLETION),
    }


def ensure_platform_badges():
    badges = []
    for definition in get_platform_badge_definitions():
        badges.append(
            ensure_badge(
                course=None,
                award_type=Badge.MILESTONE,
                criteria_key=definition["criteria_key"],
            )
        )
    return badges


def get_course_badges(course):
    badges = list(Badge.objects.filter(course=course, is_active=True))
    available_types = {badge.award_type for badge in badges}
    if Badge.ENROLLMENT not in available_types or Badge.COMPLETION not in available_types:
        ensure_course_badges(course)
        badges = list(Badge.objects.filter(course=course, is_active=True))
    return sorted(badges, key=lambda badge: BADGE_TYPE_ORDER.get(badge.award_type, 99))


def get_platform_badges():
    badges = list(Badge.objects.filter(award_type=Badge.MILESTONE, is_active=True, course__isnull=True))
    expected_count = len(get_platform_badge_definitions())
    if len(badges) < expected_count:
        ensure_platform_badges()
        badges = list(Badge.objects.filter(award_type=Badge.MILESTONE, is_active=True, course__isnull=True))
    return sorted(badges, key=lambda badge: badge.xp_reward)


@transaction.atomic
def award_badge_instance(user, badge, *, course=None):
    if is_admin_account(user):
        return None, False

    user_badge, created = UserBadge.objects.get_or_create(
        user=user,
        badge=badge,
        defaults={
            "course": course,
            "is_seen": False,
        },
    )

    updated_fields = []
    course_id = getattr(course, "id", None)
    if user_badge.course_id != course_id:
        user_badge.course = course
        updated_fields.append("course")
    if created:
        return user_badge, True
    if updated_fields:
        user_badge.save(update_fields=updated_fields)
    return user_badge, False


def award_badge(user, course, award_type):
    badge = ensure_badge(course=course, award_type=award_type)
    return award_badge_instance(user, badge, course=course)


def award_enrollment_badge(user, course):
    return award_badge(user, course, Badge.ENROLLMENT)


def award_completion_badge(user, course):
    return award_badge(user, course, Badge.COMPLETION)


def collect_user_metrics(user):
    from courses.models import Enrollment
    from progress.models import LessonProgress
    from quizzes.models import QuizAttempt

    if is_admin_account(user):
        return {
            "enrolled_courses": 0,
            "completed_courses": 0,
            "completed_lessons": 0,
            "passed_quizzes": 0,
            "perfect_quizzes": 0,
        }

    enrollments = Enrollment.objects.filter(user=user)
    return {
        "enrolled_courses": enrollments.count(),
        "completed_courses": enrollments.filter(completed_at__isnull=False).count(),
        "completed_lessons": LessonProgress.objects.filter(user=user, completed_at__isnull=False).count(),
        "passed_quizzes": QuizAttempt.objects.filter(user=user, passed=True).values("quiz_id").distinct().count(),
        "perfect_quizzes": 1 if QuizAttempt.objects.filter(user=user, score=Decimal("100.00")).exists() else 0,
    }


def sync_platform_badges(user):
    if is_admin_account(user):
        return []

    metrics = collect_user_metrics(user)
    new_awards = []

    for badge in get_platform_badges():
        target = badge.visual_spec.get("target", 1)
        metric_name = badge.visual_spec.get("metric")
        progress_value = metrics.get(metric_name, 0)
        if progress_value < target:
            continue
        award, created = award_badge_instance(user, badge, course=None)
        if created:
            new_awards.append(award)

    return new_awards


def sync_user_achievement_state(user):
    from courses.models import Enrollment

    if is_admin_account(user):
        return []

    enrollments = list(Enrollment.objects.filter(user=user).select_related("course"))
    for enrollment in enrollments:
        ensure_course_badges(enrollment.course)
        award_enrollment_badge(user, enrollment.course)
        if enrollment.completed_at:
            award_completion_badge(user, enrollment.course)

    return sync_platform_badges(user)


def xp_threshold_for_level(level):
    if level <= 1:
        return 0

    total = 0
    for current_level in range(1, level):
        total += 120 + ((current_level - 1) * 40)
    return total


def build_level_summary(total_xp):
    level = 1
    while total_xp >= xp_threshold_for_level(level + 1):
        level += 1

    current_floor = xp_threshold_for_level(level)
    next_floor = xp_threshold_for_level(level + 1)
    current_span = max(next_floor - current_floor, 1)
    progress_in_level = total_xp - current_floor
    progress_percent = min(100, int((progress_in_level / current_span) * 100))

    return {
        "level": level,
        "total_xp": total_xp,
        "current_floor": current_floor,
        "next_floor": next_floor,
        "progress_in_level": progress_in_level,
        "progress_percent": progress_percent,
        "xp_to_next_level": max(next_floor - total_xp, 0),
        "next_level": level + 1,
        "current_span": current_span,
    }


def get_badge_state(*, award, progress_value, target_value):
    if award:
        return {
            "status": "earned",
            "status_label": "Unlocked",
            "helper_text": "Ready in your collection.",
        }

    if progress_value > 0:
        return {
            "status": "in_progress",
            "status_label": "In Progress",
            "helper_text": "Keep going to unlock this reward.",
        }

    return {
        "status": "locked",
        "status_label": "Locked",
        "helper_text": "Start the matching milestone to make progress.",
    }


def build_badge_payload(*, badge, award=None, progress_value=0, target_value=1, helper_text=None):
    safe_target = max(target_value, 1)
    safe_progress = min(progress_value, safe_target)
    state = get_badge_state(award=award, progress_value=safe_progress, target_value=safe_target)
    return {
        "badge": badge,
        "award": award,
        "progress_value": safe_progress,
        "target_value": safe_target,
        "progress_percent": int((safe_progress / safe_target) * 100),
        "progress_text": f"{safe_progress}/{safe_target}",
        "xp_reward": badge.xp_reward,
        "helper_text": helper_text or state["helper_text"],
        **state,
    }


def build_course_badge_track(user, course, *, enrollment=None, awards=None):
    from progress.models import LessonProgress

    badges = get_course_badges(course)
    award_map = awards or {}
    lesson_total = max(course.lessons.filter(is_published=True).count(), 1)
    completed_lessons = 0
    if getattr(user, "is_authenticated", False) and enrollment:
        completed_lessons = LessonProgress.objects.filter(
            user=user,
            lesson__course=course,
            completed_at__isnull=False,
        ).count()

    track = []
    for badge in badges:
        award = award_map.get(badge.id)
        if badge.award_type == Badge.ENROLLMENT:
            helper_text = "Enrollment instantly unlocks this starter badge."
            track.append(
                build_badge_payload(
                    badge=badge,
                    award=award,
                    progress_value=1 if enrollment else 0,
                    target_value=1,
                    helper_text=helper_text,
                )
            )
            continue

        helper_text = "Complete every lesson and pass the final quiz to claim this badge."
        track.append(
            build_badge_payload(
                badge=badge,
                award=award,
                progress_value=lesson_total if award else completed_lessons if enrollment else 0,
                target_value=lesson_total,
                helper_text=helper_text,
            )
        )

    return track


def build_badge_track(user, course, *, enrollment=None, awards=None):
    if is_admin_account(user):
        return []

    return build_course_badge_track(user, course, enrollment=enrollment, awards=awards)


def build_platform_badge_track(user, *, awards=None, metrics=None):
    if is_admin_account(user):
        return []

    badge_map = awards or {}
    snapshot = metrics or collect_user_metrics(user)

    track = []
    for badge in get_platform_badges():
        metric_name = badge.visual_spec.get("metric")
        target = badge.visual_spec.get("target", 1)
        current_value = snapshot.get(metric_name, 0)
        award = badge_map.get(badge.id)
        track.append(
            build_badge_payload(
                badge=badge,
                award=award,
                progress_value=target if award else current_value,
                target_value=target,
                helper_text=f"Goal: {badge.description}",
            )
        )

    return sorted(
        track,
        key=lambda item: (
            BADGE_STATUS_ORDER.get(item["status"], 9),
            -item["progress_percent"],
            -item["xp_reward"],
        ),
    )


def build_user_achievement_summary(user, *, awards=None):
    if is_admin_account(user):
        return {
            "level": 1,
            "total_xp": 0,
            "current_floor": 0,
            "next_floor": 120,
            "progress_in_level": 0,
            "progress_percent": 0,
            "xp_to_next_level": 120,
            "next_level": 2,
            "current_span": 120,
            "earned_badges": 0,
            "milestone_badges": 0,
            "course_badges": 0,
            "latest_awards": [],
        }

    award_list = list(
        awards
        if awards is not None
        else UserBadge.objects.filter(user=user).select_related("badge", "course", "badge__course")
    )
    total_xp = sum(award.badge.xp_reward for award in award_list)
    level_summary = build_level_summary(total_xp)
    milestone_count = sum(1 for award in award_list if award.badge.award_type == Badge.MILESTONE)
    course_badge_count = len(award_list) - milestone_count
    return {
        **level_summary,
        "earned_badges": len(award_list),
        "milestone_badges": milestone_count,
        "course_badges": course_badge_count,
        "latest_awards": award_list[:4],
    }


def group_awards_by_course(awards):
    awards_by_course = defaultdict(dict)
    for award in awards:
        if award.course_id:
            awards_by_course[award.course_id][award.badge_id] = award
    return awards_by_course


def group_milestone_awards(awards):
    return {
        award.badge_id: award
        for award in awards
        if award.badge.award_type == Badge.MILESTONE
    }
