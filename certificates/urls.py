from django.urls import path

from .views import certificate_detail, certificate_download, certificate_list


urlpatterns = [
    path("", certificate_list, name="certificate_list"),
    path("<int:pk>/", certificate_detail, name="certificate_detail"),
    path("<int:pk>/download/", certificate_download, name="certificate_download"),
]
