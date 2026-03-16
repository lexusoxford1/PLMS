from django.urls import path

from .views import api_course_list, api_course_progress, api_submit_lesson_activity


urlpatterns = [
    path("courses/", api_course_list, name="api_course_list"),
    path("courses/<slug:slug>/progress/", api_course_progress, name="api_course_progress"),
    path(
        "courses/<slug:course_slug>/lessons/<slug:lesson_slug>/submit-activity/",
        api_submit_lesson_activity,
        name="api_submit_lesson_activity",
    ),
]
