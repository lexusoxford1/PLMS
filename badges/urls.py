from django.urls import path

from .views import badge_list


urlpatterns = [
    path("", badge_list, name="badge_list"),
]
