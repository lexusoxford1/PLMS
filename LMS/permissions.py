from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect


ADMIN_ROLE = "admin"
LEARNER_ACCESS_DENIED_MESSAGE = (
    "Admin accounts are reserved for system management and cannot access learner features."
)


def _prefixed(field_name, prefix=""):
    return f"{prefix}{field_name}" if prefix else field_name


def admin_account_q(prefix=""):
    return (
        Q(**{_prefixed("is_superuser", prefix): True})
        | Q(**{_prefixed("is_staff", prefix): True})
        | Q(**{_prefixed("role", prefix): ADMIN_ROLE})
    )


def learner_account_q(prefix=""):
    return (
        Q(**{_prefixed("is_superuser", prefix): False, _prefixed("is_staff", prefix): False})
        & ~Q(**{_prefixed("role", prefix): ADMIN_ROLE})
    )


def is_admin_account(user):
    return bool(
        getattr(user, "is_authenticated", False)
        and (user.is_superuser or user.is_staff or getattr(user, "role", "") == ADMIN_ROLE)
    )


def can_access_learner_features(user):
    return bool(getattr(user, "is_authenticated", False) and not is_admin_account(user))


def get_management_redirect_name(user):
    return "adminpanel:dashboard" if getattr(user, "is_superuser", False) else "home"


def learner_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not can_access_learner_features(request.user):
            messages.error(request, LEARNER_ACCESS_DENIED_MESSAGE)
            return redirect(get_management_redirect_name(request.user))
        return view_func(request, *args, **kwargs)

    return wrapped


def learner_api_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication required."}, status=401)
        if not can_access_learner_features(request.user):
            return JsonResponse({"detail": LEARNER_ACCESS_DENIED_MESSAGE}, status=403)
        return view_func(request, *args, **kwargs)

    return wrapped


class LearnerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return can_access_learner_features(self.request.user)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, LEARNER_ACCESS_DENIED_MESSAGE)
            return redirect(get_management_redirect_name(self.request.user))
        return super().handle_no_permission()


class AdminRequiredMixin(UserPassesTestMixin):
    """Restrict a view to admin-class accounts."""

    def test_func(self):
        user = self.request.user
        return is_admin_account(user)
