from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from courses.models import Course

from .serializers import serialize_course


def api_course_list(request):
    courses = Course.objects.filter(is_published=True).prefetch_related("lessons")
    payload = [serialize_course(course, request.user if request.user.is_authenticated else None) for course in courses]
    return JsonResponse({"courses": payload})


@login_required
def api_course_progress(request, slug):
    course = get_object_or_404(Course.objects.prefetch_related("lessons"), slug=slug, is_published=True)
    return JsonResponse(serialize_course(course, request.user))
