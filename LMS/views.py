from django.views.generic import TemplateView

from badges.models import UserBadge
from badges.services import (
    build_badge_track,
    build_platform_badge_track,
    build_user_achievement_summary,
    group_awards_by_course,
    group_milestone_awards,
    sync_user_achievement_state,
)
from certificates.models import Certificate
from courses.models import Course, Enrollment
from quizzes.models import QuizAttempt

from .permissions import LearnerRequiredMixin, is_admin_account
from .utils import build_course_outline, course_completion_percentage


HOME_COURSE_THEMES = {
    "csharp": {
        "language_key": "csharp",
        "language_label": "C#",
        "theme_class": "landing-course-card--csharp",
        "track_summary": "Progressive C# fundamentals with clear syntax, logic, and problem-solving milestones.",
    },
    "php": {
        "language_key": "php",
        "language_label": "PHP",
        "theme_class": "landing-course-card--php",
        "track_summary": "Server-side logic, practical scripting, and beginner-friendly web programming flow.",
    },
    "python": {
        "language_key": "python",
        "language_label": "Python",
        "theme_class": "landing-course-card--python",
        "track_summary": "Clean Python syntax, guided practice, and beginner momentum toward real coding confidence.",
    },
    "default": {
        "language_key": "general",
        "language_label": "Programming",
        "theme_class": "landing-course-card--default",
        "track_summary": "Structured lessons with guided progression, checkpoints, and certificate-ready outcomes.",
    },
}


def _get_home_course_theme(course):
    title = course.title.lower()
    slug = course.slug.lower()
    if "c#" in title or "csharp" in slug:
        return HOME_COURSE_THEMES["csharp"]
    if "php" in title or "php" in slug:
        return HOME_COURSE_THEMES["php"]
    if "python" in title or "python" in slug:
        return HOME_COURSE_THEMES["python"]
    return HOME_COURSE_THEMES["default"]


class HomeView(TemplateView):
    template_name = "LMS/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        published_courses = list(Course.objects.filter(is_published=True).prefetch_related("lessons"))
        featured_courses = published_courses[:6]
        enrolled_course_ids = set()
        is_admin_viewer = is_admin_account(self.request.user)
        if self.request.user.is_authenticated and not is_admin_viewer:
            enrolled_course_ids = set(
                Enrollment.objects.filter(user=self.request.user, course__in=featured_courses).values_list("course_id", flat=True)
            )

        featured_course_rows = []
        for course in featured_courses:
            lesson_count = sum(1 for lesson in course.lessons.all() if lesson.is_published)
            progress_percent = course_completion_percentage(self.request.user, course)
            is_enrolled = course.id in enrolled_course_ids
            if is_admin_viewer:
                cta_label = "Open Admin Panel"
                status_label = "Admin view"
                progress_note = "Manage course content and learner activity from the admin workspace."
            elif progress_percent >= 100:
                cta_label = "Review Course"
                status_label = "Certificate ready"
                progress_note = "Finished and ready to revisit"
            elif is_enrolled and progress_percent > 0:
                cta_label = "Continue Course"
                status_label = "In progress"
                progress_note = "Pick up where you left off"
            elif is_enrolled:
                cta_label = "Start Course"
                status_label = "Enrolled"
                progress_note = "Ready for your first lesson"
            else:
                cta_label = "View Course"
                status_label = course.get_difficulty_display()
                progress_note = "Preview the full guided path"

            featured_course_rows.append(
                {
                    "course": course,
                    "lesson_count": lesson_count,
                    "progress_percent": progress_percent,
                    "is_enrolled": is_enrolled,
                    "cta_label": cta_label,
                    "status_label": status_label,
                    "progress_note": progress_note,
                    **_get_home_course_theme(course),
                }
            )

        context["featured_courses"] = featured_courses
        context["featured_course_rows"] = featured_course_rows
        context["published_course_count"] = len(published_courses)
        context["published_lesson_count"] = sum(
            sum(1 for lesson in course.lessons.all() if lesson.is_published) for course in published_courses
        )
        context["published_hours"] = sum(course.estimated_hours for course in published_courses)
        context["is_admin_viewer"] = is_admin_viewer
        return context


class DashboardView(LearnerRequiredMixin, TemplateView):
    template_name = "LMS/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sync_user_achievement_state(self.request.user)
        enrollments = (
            Enrollment.objects.filter(user=self.request.user)
            .select_related("course")
            .prefetch_related("course__lessons", "course__badges")
            .order_by("-enrolled_at")
        )
        user_badges = list(
            UserBadge.objects.filter(user=self.request.user)
            .select_related("badge", "badge__course", "course")
            .order_by("-awarded_at")
        )
        awards_by_course = group_awards_by_course(user_badges)
        milestone_awards = group_milestone_awards(user_badges)

        dashboard_courses = []
        for enrollment in enrollments:
            badge_track = build_badge_track(
                self.request.user,
                enrollment.course,
                enrollment=enrollment,
                awards=awards_by_course.get(enrollment.course_id, {}),
            )
            unlocked_badges = [item for item in badge_track if item["status"] == "earned"]
            next_badge = next((item for item in badge_track if item["status"] != "earned"), None)
            dashboard_courses.append(
                {
                    "course": enrollment.course,
                    "progress_percent": course_completion_percentage(self.request.user, enrollment.course),
                    "outline": build_course_outline(self.request.user, enrollment.course),
                    "completed_at": enrollment.completed_at,
                    "badge_track": badge_track,
                    "unlocked_badge_count": len(unlocked_badges),
                    "total_badge_count": len(badge_track),
                    "earned_xp": sum(item["xp_reward"] for item in unlocked_badges),
                    "total_xp": sum(item["xp_reward"] for item in badge_track),
                    "next_badge": next_badge,
                }
            )

        context["dashboard_courses"] = dashboard_courses
        context["recent_attempts"] = QuizAttempt.objects.filter(user=self.request.user).select_related(
            "quiz__lesson__course"
        )[:5]
        context["badges"] = user_badges[:6]
        context["badge_count"] = len(user_badges)
        context["achievement_summary"] = build_user_achievement_summary(self.request.user, awards=user_badges)
        context["platform_badges"] = build_platform_badge_track(
            self.request.user,
            awards=milestone_awards,
        )
        context["completed_milestone_count"] = sum(
            1 for item in context["platform_badges"] if item["status"] == "earned"
        )
        certificates = list(Certificate.objects.filter(user=self.request.user).select_related("course"))
        context["certificates"] = certificates[:6]
        context["certificate_count"] = len(certificates)
        context["recent_badges"] = user_badges[:3]
        return context
