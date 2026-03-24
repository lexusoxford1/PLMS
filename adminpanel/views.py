from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import TemplateView

from .forms import AdminLoginForm
from .mixins import ADMIN_PANEL_ACCESS_DENIED_MESSAGE, AdminPanelAccessMixin


ADMIN_NAV_ITEMS = [
    {"key": "dashboard", "label": "Dashboard", "url_name": "adminpanel:dashboard"},
    {"key": "courses", "label": "Courses", "url_name": "adminpanel:courses"},
    {"key": "lectures", "label": "Lectures", "url_name": "adminpanel:lectures"},
    {"key": "materials", "label": "Materials", "url_name": "adminpanel:materials"},
    {"key": "activities", "label": "Activities", "url_name": "adminpanel:activities"},
    {"key": "progress", "label": "Progress", "url_name": "adminpanel:progress"},
    {"key": "users", "label": "Users", "url_name": "adminpanel:users"},
    {"key": "badges", "label": "Badges", "url_name": "adminpanel:badges"},
    {"key": "certificates", "label": "Certificates", "url_name": "adminpanel:certificates"},
]


def _get_safe_admin_redirect(request):
    redirect_to = request.POST.get("next") or request.GET.get("next") or ""
    if redirect_to and url_has_allowed_host_and_scheme(
        url=redirect_to,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect_to
    return reverse("adminpanel:dashboard")


def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect(_get_safe_admin_redirect(request))

    form = AdminLoginForm(request.POST or None)
    next_url = request.POST.get("next") or request.GET.get("next") or ""

    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user is None:
            form.add_error(None, "Invalid username or password.")
        elif not user.is_superuser:
            form.add_error(None, ADMIN_PANEL_ACCESS_DENIED_MESSAGE)
        else:
            login(request, user)
            return redirect(_get_safe_admin_redirect(request))

    return render(
        request,
        "adminpanel/login.html",
        {
            "form": form,
            "next": next_url,
        },
    )


class AdminPanelPageView(AdminPanelAccessMixin, TemplateView):
    section_key = "dashboard"
    page_title = "Admin Panel"
    page_description = "Manage learning operations from one responsive workspace."
    template_name = "adminpanel/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["admin_nav_items"] = ADMIN_NAV_ITEMS
        context["admin_active_section"] = self.section_key
        context["admin_page_title"] = self.page_title
        context["admin_page_description"] = self.page_description
        return context


class DashboardView(AdminPanelPageView):
    section_key = "dashboard"
    page_title = "Admin Dashboard"
    page_description = "Watch platform health, learner activity, and course enrollment trends."
    template_name = "adminpanel/dashboard.html"


class CoursesView(AdminPanelPageView):
    section_key = "courses"
    page_title = "Course Management"
    page_description = "Create, organize, filter, and publish programming tracks with clear category-based classification and thumbnails."
    template_name = "adminpanel/courses.html"


class LecturesView(AdminPanelPageView):
    section_key = "lectures"
    page_title = "Lecture Management"
    page_description = "Maintain lecture structure, rich text content, images, and publishing order per course."
    template_name = "adminpanel/lectures.html"


class MaterialsView(AdminPanelPageView):
    section_key = "materials"
    page_title = "Learning Materials"
    page_description = "Manage lecture attachments, uploaded decks, Canva links, Google Slides, and learner-facing presentation viewers."
    template_name = "adminpanel/materials.html"


class ActivitiesView(AdminPanelPageView):
    section_key = "activities"
    page_title = "Activities and Quizzes"
    page_description = "Configure coding validations, passing conditions, quiz rules, and assessment content."
    template_name = "adminpanel/activities.html"


class ProgressView(AdminPanelPageView):
    section_key = "progress"
    page_title = "User Progress"
    page_description = "Review lesson completion, activity validation, quiz passes, and course progress in one place."
    template_name = "adminpanel/progress.html"


class UsersView(AdminPanelPageView):
    section_key = "users"
    page_title = "User and Role Management"
    page_description = "Manage learner and admin accounts while preserving strict separation between system operators and learners."
    template_name = "adminpanel/users.html"


class BadgesView(AdminPanelPageView):
    section_key = "badges"
    page_title = "Badge Management"
    page_description = "Create and maintain achievement badges, XP rewards, and course or platform incentives."
    template_name = "adminpanel/badges.html"


class CertificatesView(AdminPanelPageView):
    section_key = "certificates"
    page_title = "Certificates"
    page_description = "Monitor issued certificates and manually refresh or resend them when needed."
    template_name = "adminpanel/certificates.html"
