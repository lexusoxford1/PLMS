from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from badges.models import UserBadge
from certificates.models import Certificate
from courses.models import Course, Enrollment
from quizzes.models import QuizAttempt

from .utils import build_course_outline, course_completion_percentage


class HomeView(TemplateView):
    template_name = "LMS/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_courses"] = Course.objects.filter(is_published=True).prefetch_related("lessons")[:6]
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "LMS/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enrollments = (
            Enrollment.objects.filter(user=self.request.user)
            .select_related("course")
            .prefetch_related("course__lessons")
            .order_by("-enrolled_at")
        )
        dashboard_courses = []
        for enrollment in enrollments:
            dashboard_courses.append(
                {
                    "course": enrollment.course,
                    "progress_percent": course_completion_percentage(self.request.user, enrollment.course),
                    "outline": build_course_outline(self.request.user, enrollment.course),
                    "completed_at": enrollment.completed_at,
                }
            )

        context["dashboard_courses"] = dashboard_courses
        context["recent_attempts"] = QuizAttempt.objects.filter(user=self.request.user).select_related(
            "quiz__lesson__course"
        )[:5]
        context["badges"] = UserBadge.objects.filter(user=self.request.user).select_related("badge", "course")[:6]
        context["certificates"] = Certificate.objects.filter(user=self.request.user).select_related("course")[:6]
        return context
