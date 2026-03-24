from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy


ADMIN_PANEL_ACCESS_DENIED_MESSAGE = "Only Django superusers can access the Admin Panel."
ADMIN_PANEL_LOGIN_URL = reverse_lazy("adminpanel:login")


def can_access_admin_panel(user):
    return bool(getattr(user, "is_authenticated", False) and user.is_superuser)


class AdminPanelAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = False
    login_url = ADMIN_PANEL_LOGIN_URL
    redirect_field_name = "next"

    def test_func(self):
        return can_access_admin_panel(self.request.user)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, ADMIN_PANEL_ACCESS_DENIED_MESSAGE)
            return redirect("home")
        return super().handle_no_permission()
