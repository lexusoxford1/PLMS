from django.urls import path

from .views import (
    course_detail,
    course_list,
    enroll_course,
    lesson_detail,
    mark_lecture_complete,
    submit_activity,
)


urlpatterns = [
    path("", course_list, name="course_list"),
    path("<slug:slug>/", course_detail, name="course_detail"),
    path("<slug:slug>/enroll/", enroll_course, name="enroll_course"),
    path("<slug:course_slug>/lessons/<slug:lesson_slug>/", lesson_detail, name="lesson_detail"),
    path(
        "<slug:course_slug>/lessons/<slug:lesson_slug>/complete-lecture/",
        mark_lecture_complete,
        name="mark_lecture_complete",
    ),
    path(
        "<slug:course_slug>/lessons/<slug:lesson_slug>/submit-activity/",
        submit_activity,
        name="submit_activity",
    ),
]
