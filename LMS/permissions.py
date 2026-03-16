from django.contrib.auth.mixins import UserPassesTestMixin


class AdminRequiredMixin(UserPassesTestMixin):
    """Restrict a view to staff users and custom admin-role users."""

    def test_func(self):
        user = self.request.user
        return bool(user.is_authenticated and (user.is_staff or getattr(user, "role", "") == "admin"))
