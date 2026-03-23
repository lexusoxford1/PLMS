"""Root URL configuration for the PLMS project."""

from adminpanel import urls as adminpanel_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "admin-panel/",
        include((adminpanel_urls.urlpatterns, adminpanel_urls.app_name), namespace=adminpanel_urls.app_name),
    ),
    path("", include("LMS.urls")),
    path("accounts/", include("users.urls")),
    path("accounts/", include("allauth.urls")),
    path("courses/", include("courses.urls")),
    path("quizzes/", include("quizzes.urls")),
    path("badges/", include("badges.urls")),
    path("certificates/", include("certificates.urls")),
    path("api/", include("api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
