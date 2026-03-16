from django.urls import path

from .views import api_course_list, api_course_progress


urlpatterns = [
    path("courses/", api_course_list, name="api_course_list"),
    path("courses/<slug:slug>/progress/", api_course_progress, name="api_course_progress"),
]
