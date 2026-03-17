from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from courses.models import Course, Enrollment

from .models import UserBadge
from .services import (
    build_badge_track,
    build_platform_badge_track,
    build_user_achievement_summary,
    group_awards_by_course,
    group_milestone_awards,
    sync_user_achievement_state,
)


@login_required
def badge_list(request):
    sync_user_achievement_state(request.user)
    user_badges = list(
        UserBadge.objects.filter(user=request.user)
        .select_related("badge", "badge__course", "course")
        .order_by("-awarded_at")
    )
    enrollments = {
        enrollment.course_id: enrollment
        for enrollment in Enrollment.objects.filter(user=request.user).select_related("course")
    }
    awards_by_course = group_awards_by_course(user_badges)
    milestone_awards = group_milestone_awards(user_badges)

    course_collections = []
    for course in Course.objects.filter(is_published=True).prefetch_related("badges").order_by("title"):
        track = build_badge_track(
            request.user,
            course,
            enrollment=enrollments.get(course.id),
            awards=awards_by_course.get(course.id, {}),
        )
        course_collections.append(
            {
                "course": course,
                "track": track,
                "xp_total": sum(item["xp_reward"] for item in track),
            }
        )

    platform_badges = build_platform_badge_track(request.user, awards=milestone_awards)
    earned_completion_count = sum(1 for award in user_badges if award.badge.award_type == award.badge.COMPLETION)
    context = {
        "badges": user_badges,
        "badge_count": len(user_badges),
        "completion_badge_count": earned_completion_count,
        "enrollment_badge_count": sum(1 for award in user_badges if award.badge.award_type == award.badge.ENROLLMENT),
        "milestone_badge_count": sum(1 for award in user_badges if award.badge.award_type == award.badge.MILESTONE),
        "total_badge_count": sum(len(collection["track"]) for collection in course_collections)
        + len(platform_badges),
        "course_collections": course_collections,
        "platform_badges": platform_badges,
        "achievement_summary": build_user_achievement_summary(request.user, awards=user_badges),
        "featured_platform_badge": next(
            (item for item in platform_badges if item["status"] != "earned"),
            platform_badges[0] if platform_badges else None,
        ),
    }
    return render(request, "badges/badge_list.html", context)
