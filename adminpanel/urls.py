from django.urls import include, path

from .views import (
    ActivitiesView,
    BadgesView,
    CertificatesView,
    CoursesView,
    DashboardView,
    LecturesView,
    MaterialsView,
    ProgressView,
    UsersView,
    admin_login_view,
)


app_name = "adminpanel"

urlpatterns = [
    path("login/", admin_login_view, name="login"),
    path("", DashboardView.as_view(), name="dashboard"),
    path("courses/", CoursesView.as_view(), name="courses"),
    path("lectures/", LecturesView.as_view(), name="lectures"),
    path("materials/", MaterialsView.as_view(), name="materials"),
    path("activities/", ActivitiesView.as_view(), name="activities"),
    path("progress/", ProgressView.as_view(), name="progress"),
    path("users/", UsersView.as_view(), name="users"),
    path("badges/", BadgesView.as_view(), name="badges"),
    path("certificates/", CertificatesView.as_view(), name="certificates"),
    path("api/", include("adminpanel.api_urls")),
]
