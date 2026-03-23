import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from LMS.permissions import learner_api_required
from LMS.utils import can_access_lesson, get_or_create_lesson_progress
from courses.activity_service import submit_lesson_activity
from courses.models import Course

from .serializers import serialize_activity_submission, serialize_course


def api_course_list(request):
    courses = Course.objects.filter(is_published=True).prefetch_related("lessons")
    payload = [serialize_course(course, request.user if request.user.is_authenticated else None) for course in courses]
    return JsonResponse({"courses": payload})


@learner_api_required
def api_course_progress(request, slug):
    course = get_object_or_404(Course.objects.prefetch_related("lessons"), slug=slug, is_published=True)
    return JsonResponse(serialize_course(course, request.user))


@learner_api_required
@require_POST
def api_submit_lesson_activity(request, course_slug, lesson_slug):
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    lesson = get_object_or_404(course.lessons, slug=lesson_slug, is_published=True)

    if not can_access_lesson(request.user, lesson):
        return JsonResponse(
            {
                "notification": {
                    "level": "error",
                    "title": "Lesson locked",
                    "message": "Complete the previous lesson first to unlock this activity.",
                }
            },
            status=403,
        )

    progress = get_or_create_lesson_progress(request.user, lesson)
    if progress.activity_completed and progress.activity_result_data:
        notification = progress.activity_result_data.get("notification") or {
            "level": "info",
            "title": "Activity already completed",
            "message": "This activity has already been validated.",
        }
        return JsonResponse(
            {
                "activity": progress.activity_result_data,
                "progress": {
                    "lecture_completed": progress.lecture_completed,
                    "activity_completed": progress.activity_completed,
                    "activity_attempts": progress.activity_attempts,
                    "quiz_passed": progress.quiz_passed,
                    "lesson_completed": bool(progress.completed_at),
                    "next_lesson_unlocked": bool(progress.completed_at),
                },
                "notification": notification,
                "system_notification": notification,
            }
        )

    payload = {}
    if (request.content_type or "").startswith("application/json"):
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse(
                {
                    "notification": {
                        "level": "error",
                        "title": "Invalid request",
                        "message": "The submitted activity payload is not valid JSON.",
                    }
                },
                status=400,
            )
    else:
        payload = request.POST

    response = payload.get("response") or payload.get("code") or ""
    progress, result = submit_lesson_activity(request.user, lesson, response)
    return JsonResponse(serialize_activity_submission(course, lesson, progress, result))
