from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from courses.models import Enrollment

from LMS.utils import course_completion_percentage


@login_required
def progress_overview(request):
    enrollments = Enrollment.objects.filter(user=request.user).select_related("course").prefetch_related("course__lessons")
    progress_rows = [
        {
            "course": enrollment.course,
            "progress_percent": course_completion_percentage(request.user, enrollment.course),
            "completed_at": enrollment.completed_at,
        }
        for enrollment in enrollments
    ]
    return render(request, "LMS/dashboard.html", {"dashboard_courses": progress_rows})
