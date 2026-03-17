from .models import UserBadge
from .services import build_user_achievement_summary, sync_user_achievement_state


def pending_badge_unlocks(request):
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False):
        return {}

    sync_user_achievement_state(user)

    all_awards = list(
        UserBadge.objects.filter(user=user)
        .select_related("badge", "badge__course", "course")
        .order_by("-awarded_at")
    )
    pending_awards = list(
        award
        for award in reversed(all_awards)
        if not award.is_seen
    )
    if pending_awards:
        UserBadge.objects.filter(pk__in=[award.pk for award in pending_awards]).update(is_seen=True)
        for award in pending_awards:
            award.is_seen = True

    return {
        "pending_badge_unlocks": pending_awards,
        "user_achievement_summary": build_user_achievement_summary(user, awards=all_awards),
    }
