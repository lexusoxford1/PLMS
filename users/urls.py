from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import ProviderAwareLoginView, RegisterView, profile_view


urlpatterns = [
    path("login/", ProviderAwareLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", profile_view, name="profile"),
]
