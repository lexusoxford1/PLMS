from collections import Counter
from math import cos, pi, sin

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.views import LoginView
from django.db.models import Prefetch
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView

from LMS.permissions import is_admin_account, learner_required
from badges.catalog import get_platform_badge_definitions
from badges.models import UserBadge
from badges.services import (
    build_platform_badge_track,
    build_user_achievement_summary,
    group_milestone_awards,
    sync_user_achievement_state,
)
from certificates.models import Certificate
from courses.models import Enrollment, Lesson
from progress.models import LessonProgress
from quizzes.models import QuizAttempt

from .forms import ProfilePasswordForm, UserProfileForm, UserRegistrationForm

PROFILE_PANELS = {"overview", "learning", "achievements", "settings", "security"}
MANUAL_AUTH_BACKEND = "django.contrib.auth.backends.ModelBackend"


def _clamp_percent(value):
    return max(0, min(100, int(round(value))))


def _safe_percent(value, total):
    if total <= 0:
        return 0
    return _clamp_percent((value / total) * 100)


def _build_profile_completion(user):
    certificate_identity_ready = bool(
        user.certificate_name.strip() or user.get_full_name().strip()
    )
    checkpoints = [
        ("Profile photo", bool(user.profile_picture)),
        ("Full name", bool(user.get_full_name().strip())),
        ("Role or title", bool(user.title.strip())),
        ("Bio", bool(user.bio.strip())),
        ("Email", bool(user.email.strip())),
        ("Phone", bool(user.phone_number.strip())),
        ("Certificate profile", certificate_identity_ready),
    ]
    completed = sum(1 for _, is_complete in checkpoints if is_complete)
    return {
        "checkpoints": [
            {"label": label, "complete": is_complete}
            for label, is_complete in checkpoints
        ],
        "percent": _safe_percent(completed, len(checkpoints)),
    }


def _build_profile_metrics(*, achievement_summary, analytics_average, certificate_count, joined_at):
    now = timezone.now()
    months_active = max(
        1,
        ((now.year - joined_at.year) * 12) + (now.month - joined_at.month) + 1,
    )
    return [
        {
            "label": "Skill score",
            "value": f"{analytics_average}%",
        },
        {
            "label": "Experience",
            "value": f"{months_active} mo",
        },
        {
            "label": "Certificates",
            "value": str(certificate_count),
        },
        {
            "label": "Total XP",
            "value": str(achievement_summary["total_xp"]),
        },
    ]


def _build_radar_chart(axes):
    center_x = 170
    center_y = 168
    radius = 112
    label_radius = 145
    count = max(len(axes), 1)
    grid = []
    chart_axes = []
    points = []

    for scale in (25, 50, 75, 100):
        ring_points = []
        for index in range(count):
            angle = (-pi / 2) + ((2 * pi * index) / count)
            ring_x = center_x + ((radius * scale / 100) * cos(angle))
            ring_y = center_y + ((radius * scale / 100) * sin(angle))
            ring_points.append(f"{ring_x:.2f},{ring_y:.2f}")
        grid.append(" ".join(ring_points))

    for index, axis in enumerate(axes):
        angle = (-pi / 2) + ((2 * pi * index) / count)
        outer_x = center_x + (radius * cos(angle))
        outer_y = center_y + (radius * sin(angle))
        label_x = center_x + (label_radius * cos(angle))
        label_y = center_y + (label_radius * sin(angle))
        point_x = center_x + ((radius * axis["value"] / 100) * cos(angle))
        point_y = center_y + ((radius * axis["value"] / 100) * sin(angle))

        chart_axes.append(
            {
                **axis,
                "outer_x": f"{outer_x:.2f}",
                "outer_y": f"{outer_y:.2f}",
                "label_x": f"{label_x:.2f}",
                "label_y": f"{label_y:.2f}",
                "point_x": f"{point_x:.2f}",
                "point_y": f"{point_y:.2f}",
                "label_anchor": "middle"
                if abs(label_x - center_x) < 24
                else "start"
                if label_x > center_x
                else "end",
            }
        )
        points.append(f"{point_x:.2f},{point_y:.2f}")

    return {
        "center_x": center_x,
        "center_y": center_y,
        "grid": grid,
        "axes": chart_axes,
        "points": " ".join(points),
    }


def _build_analytics(
    *,
    enrollments,
    completed_lessons_by_course,
    progress_records,
    user_badges,
    certificates,
    attempts,
    profile_completion_percent,
):
    total_courses = len(enrollments)
    completed_courses = sum(1 for enrollment in enrollments if enrollment.completed_at)
    active_course_ids = {progress.lesson.course_id for progress in progress_records}
    total_lessons = 0
    completed_lessons = 0
    progress_values = []

    for enrollment in enrollments:
        lesson_total = len(enrollment.course.lessons.all())
        completed_total = completed_lessons_by_course.get(enrollment.course_id, 0)
        total_lessons += lesson_total
        completed_lessons += completed_total
        progress_values.append(_safe_percent(completed_total, lesson_total))

    average_progress = round(sum(progress_values) / len(progress_values)) if progress_values else 0
    average_quiz_score = round(
        sum(float(attempt.score) for attempt in attempts) / len(attempts)
    ) if attempts else 0
    total_available_badges = (total_courses * 2) + len(get_platform_badge_definitions())
    certificate_coverage = (
        _safe_percent(len(certificates), completed_courses)
        if completed_courses
        else average_progress
    )

    axes = [
        {
            "label": "Course mastery",
            "value": average_progress,
            "summary": "Average progress across enrolled courses.",
        },
        {
            "label": "Quiz confidence",
            "value": average_quiz_score,
            "summary": "Average assessment score from quiz attempts.",
        },
        {
            "label": "Practice depth",
            "value": _safe_percent(completed_lessons, total_lessons),
            "summary": "Lessons fully completed and validated.",
        },
        {
            "label": "Consistency",
            "value": _clamp_percent(
                (
                    (_safe_percent(len(active_course_ids), total_courses) * 0.4)
                    + (_safe_percent(completed_courses, total_courses) * 0.6)
                )
                if total_courses
                else 0
            ),
            "summary": "How steadily learning activity turns into completions.",
        },
        {
            "label": "Achievements",
            "value": _safe_percent(len(user_badges), total_available_badges),
            "summary": "Unlocked badges and platform milestones so far.",
        },
        {
            "label": "Certificate ready",
            "value": _clamp_percent(
                (profile_completion_percent * 0.45) + (certificate_coverage * 0.55)
            ),
            "summary": "Profile completeness plus certificate issuance coverage.",
        },
    ]

    return {
        "axes": axes,
        "average": round(sum(axis["value"] for axis in axes) / len(axes)) if axes else 0,
        "chart": _build_radar_chart(axes),
    }


def _build_learning_history(enrollments, completed_lessons_by_course, certificate_map):
    history = []
    total_learning_hours = 0

    for enrollment in enrollments:
        lesson_total = len(enrollment.course.lessons.all())
        completed_lessons = completed_lessons_by_course.get(enrollment.course_id, 0)
        progress_percent = _safe_percent(completed_lessons, lesson_total)
        total_learning_hours += enrollment.course.estimated_hours * (progress_percent / 100)
        certificate = certificate_map.get(enrollment.course_id)

        if certificate and certificate.issued_at:
            status_label = "Certified"
            status_tone = "success"
        elif enrollment.completed_at:
            status_label = "Ready"
            status_tone = "warning"
        else:
            status_label = "In progress"
            status_tone = "neutral"

        history.append(
            {
                "course": enrollment.course,
                "duration": enrollment.course.estimated_hours,
                "progress_percent": progress_percent,
                "completed_at": enrollment.completed_at,
                "certificate": certificate,
                "status_label": status_label,
                "status_tone": status_tone,
            }
        )

    return history, round(total_learning_hours, 1)


def _build_learning_statistics(
    *,
    total_learning_hours,
    completed_courses,
    certificates,
    completed_lessons,
    attempts,
    achievement_summary,
):
    average_quiz_score = round(
        sum(float(attempt.score) for attempt in attempts) / len(attempts)
    ) if attempts else 0
    return [
        {"label": "Total learning hours", "value": f"{total_learning_hours:g}h"},
        {"label": "Completed courses", "value": str(completed_courses)},
        {"label": "Certifications", "value": str(len(certificates))},
        {"label": "Lessons mastered", "value": str(completed_lessons)},
        {"label": "Average quiz score", "value": f"{average_quiz_score}%"},
        {"label": "Badge XP earned", "value": str(achievement_summary["total_xp"])},
    ]


def _build_achievement_cards(platform_badges):
    cards = []
    for item in platform_badges[:4]:
        spec = item["badge"].visual_spec
        cards.append(
            {
                **item,
                "glyph": spec.get("glyph", item["badge"].name[:2].upper()),
                "accent_label": spec.get("accent_label", "Achievement"),
                "theme_style": "; ".join(
                    [
                        f"--achievement-primary: {spec['primary']}",
                        f"--achievement-secondary: {spec['secondary']}",
                        f"--achievement-accent: {spec['accent']}",
                        f"--achievement-surface: {spec['surface']}",
                        f"--achievement-ink: {spec['ink']}",
                    ]
                ),
            }
        )
    return cards


def _refresh_user_certificate_artifacts(user):
    for certificate in Certificate.objects.filter(user=user).select_related(
        "course",
        "course__created_by",
        "badge",
    ):
        certificate.refresh_artifact()


class ProviderAwareLoginView(LoginView):
    template_name = "auth/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["social_providers"] = settings.SOCIAL_LOGIN_PROVIDERS
        return context

    def get_success_url(self):
        if is_admin_account(self.request.user):
            return reverse("adminpanel:dashboard") if self.request.user.is_superuser else reverse("home")
        return super().get_success_url()


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = "auth/register.html"
    success_url = reverse_lazy("dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["social_providers"] = settings.SOCIAL_LOGIN_PROVIDERS
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object, backend=MANUAL_AUTH_BACKEND)
        messages.success(self.request, "Your PLMS account is ready. Welcome aboard.")
        return response


@learner_required
def profile_view(request):
    sync_user_achievement_state(request.user)
    active_profile_panel = request.GET.get("panel", "overview")
    if active_profile_panel not in PROFILE_PANELS:
        active_profile_panel = "overview"

    if request.method == "POST":
        action = request.POST.get("action", "profile")
        if action == "password":
            active_profile_panel = "security"
            profile_form = UserProfileForm(instance=request.user)
            password_form = ProfilePasswordForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password has been changed successfully.")
                return redirect(f"{reverse('profile')}?panel=security")
            messages.error(request, "Please correct the password fields and try again.")
        else:
            active_profile_panel = "settings"
            profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user)
            password_form = ProfilePasswordForm(user=request.user)
            if profile_form.is_valid():
                changed_fields = set(profile_form.changed_data)
                profile_form.save()
                if changed_fields.intersection(
                    {
                        "first_name",
                        "last_name",
                        "title",
                        "organization",
                        "email",
                        "certificate_name",
                    }
                ):
                    _refresh_user_certificate_artifacts(request.user)
                messages.success(
                    request,
                    "Your profile dashboard has been updated and certificate details are now in sync.",
                )
                return redirect(f"{reverse('profile')}?panel=settings")
            messages.error(request, "Please review the highlighted profile fields.")
    else:
        profile_form = UserProfileForm(instance=request.user)
        password_form = ProfilePasswordForm(user=request.user)

    user_badges = list(
        UserBadge.objects.filter(user=request.user)
        .select_related("badge", "course", "badge__course")
        .order_by("-awarded_at")
    )
    enrollments = list(
        Enrollment.objects.filter(user=request.user)
        .select_related("course")
        .prefetch_related(
            Prefetch(
                "course__lessons",
                queryset=Lesson.objects.filter(is_published=True).order_by("order"),
            )
        )
        .order_by("-enrolled_at")
    )
    progress_records = list(
        LessonProgress.objects.filter(user=request.user).select_related("lesson__course")
    )
    attempts = list(
        QuizAttempt.objects.filter(user=request.user)
        .select_related("quiz__lesson__course")
        .order_by("-attempted_at")
    )
    certificates = list(
        Certificate.objects.filter(user=request.user)
        .select_related("course", "course__created_by", "badge")
        .order_by("-issued_at", "-created_at")
    )

    completed_lessons_by_course = Counter(
        progress.lesson.course_id
        for progress in progress_records
        if progress.completed_at is not None
    )
    profile_completion = _build_profile_completion(request.user)
    milestone_awards = group_milestone_awards(user_badges)
    platform_badges = build_platform_badge_track(request.user, awards=milestone_awards)
    achievement_summary = build_user_achievement_summary(request.user, awards=user_badges)
    featured_platform_badge = next(
        (item for item in platform_badges if item["status"] != "earned"),
        platform_badges[0] if platform_badges else None,
    )
    profile_achievement_cards = _build_achievement_cards(
        [item for item in platform_badges if item is not featured_platform_badge]
    )
    analytics = _build_analytics(
        enrollments=enrollments,
        completed_lessons_by_course=completed_lessons_by_course,
        progress_records=progress_records,
        user_badges=user_badges,
        certificates=certificates,
        attempts=attempts,
        profile_completion_percent=profile_completion["percent"],
    )
    certificate_map = {certificate.course_id: certificate for certificate in certificates}
    learning_history, total_learning_hours = _build_learning_history(
        enrollments,
        completed_lessons_by_course,
        certificate_map,
    )

    return render(
        request,
        "auth/profile.html",
        {
            "profile_form": profile_form,
            "password_form": password_form,
            "social_providers": settings.SOCIAL_LOGIN_PROVIDERS,
            "achievement_summary": achievement_summary,
            "platform_badges": platform_badges,
            "achievement_cards": profile_achievement_cards,
            "featured_platform_badge": featured_platform_badge,
            "profile_completion": profile_completion,
            "profile_metrics": _build_profile_metrics(
                achievement_summary=achievement_summary,
                analytics_average=analytics["average"],
                certificate_count=len(certificates),
                joined_at=request.user.date_joined,
            ),
            "learning_analytics": analytics,
            "learning_history": learning_history[:6],
            "learning_statistics": _build_learning_statistics(
                total_learning_hours=total_learning_hours,
                completed_courses=sum(1 for enrollment in enrollments if enrollment.completed_at),
                certificates=certificates,
                completed_lessons=sum(completed_lessons_by_course.values()),
                attempts=attempts,
                achievement_summary=achievement_summary,
            ),
            "latest_certificate": certificates[0] if certificates else None,
            "recent_badges": user_badges[:4],
            "history_count": len(learning_history),
            "active_profile_panel": active_profile_panel,
        },
    )
