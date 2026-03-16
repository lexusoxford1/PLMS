from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from LMS.forms import ActivitySubmissionForm
from LMS.utils import (
    award_course_completion,
    build_course_outline,
    can_access_lesson,
    course_completion_percentage,
    get_or_create_lesson_progress,
)

from .activity_service import build_activity_concept_review, build_activity_form, submit_lesson_activity
from .models import Course, Enrollment, Lesson


def course_list(request):
    courses = Course.objects.filter(is_published=True).prefetch_related("lessons")
    course_cards = []
    for course in courses:
        course_cards.append(
            {
                "course": course,
                "progress_percent": course_completion_percentage(request.user, course),
                "is_enrolled": request.user.is_authenticated
                and Enrollment.objects.filter(user=request.user, course=course).exists(),
            }
        )
    return render(request, "courses/course_list.html", {"course_cards": course_cards})


def course_detail(request, slug):
    course = get_object_or_404(Course.objects.prefetch_related("lessons"), slug=slug, is_published=True)
    is_enrolled = request.user.is_authenticated and Enrollment.objects.filter(
        user=request.user,
        course=course,
    ).exists()
    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "outline": build_course_outline(request.user, course),
            "is_enrolled": is_enrolled,
            "progress_percent": course_completion_percentage(request.user, course),
        },
    )


@login_required
def enroll_course(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    Enrollment.objects.get_or_create(user=request.user, course=course)
    messages.success(request, f"You are now enrolled in {course.title}.")
    return redirect("course_detail", slug=course.slug)


@login_required
def lesson_detail(request, course_slug, lesson_slug):
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    lesson = get_object_or_404(Lesson, course=course, slug=lesson_slug, is_published=True)

    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.warning(request, "Please enroll in the course before opening lessons.")
        return redirect("course_detail", slug=course.slug)
    if not can_access_lesson(request.user, lesson):
        messages.warning(request, "Complete the previous lesson first to unlock this one.")
        return redirect("course_detail", slug=course.slug)

    progress = get_or_create_lesson_progress(request.user, lesson)
    next_lesson = course.lessons.filter(is_published=True, order__gt=lesson.order).order_by("order").first()
    activity_form = build_activity_form(lesson, progress)
    activity_concept_review = build_activity_concept_review(lesson)
    if progress.activity_completed:
        activity_form.fields["response"].disabled = True

    return render(
        request,
        "courses/lesson.html",
        {
            "course": course,
            "lesson": lesson,
            "progress": progress,
            "activity_form": activity_form,
            "activity_concept_review": activity_concept_review,
            "next_lesson": next_lesson,
        },
    )


@login_required
def mark_lecture_complete(request, course_slug, lesson_slug):
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    lesson = get_object_or_404(Lesson, course=course, slug=lesson_slug, is_published=True)
    if request.method == "POST" and can_access_lesson(request.user, lesson):
        progress = get_or_create_lesson_progress(request.user, lesson)
        progress.lecture_completed = True
        progress.refresh_completion_state()
        progress.save()
        if progress.completed_at is not None:
            award_course_completion(request.user, course)
        messages.success(request, "Lecture marked as complete.")
    return redirect("lesson_detail", course_slug=course.slug, lesson_slug=lesson.slug)


@login_required
def submit_activity(request, course_slug, lesson_slug):
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    lesson = get_object_or_404(Lesson, course=course, slug=lesson_slug, is_published=True)
    if not can_access_lesson(request.user, lesson):
        messages.warning(request, "This lesson is still locked.")
        return redirect("course_detail", slug=course.slug)

    progress = get_or_create_lesson_progress(request.user, lesson)
    if progress.activity_completed:
        messages.info(request, "This activity has already been completed and validated.")
        return redirect("lesson_detail", course_slug=course.slug, lesson_slug=lesson.slug)

    if request.method == "POST":
        form = ActivitySubmissionForm(request.POST)
        if form.is_valid():
            progress, result = submit_lesson_activity(request.user, lesson, form.cleaned_data["response"])
            if result.is_correct and progress.completed_at is not None:
                messages.success(request, result.title)
            else:
                messages.error(request, result.title)
        else:
            messages.error(request, "Please complete the activity response before submitting.")

    return redirect("lesson_detail", course_slug=course.slug, lesson_slug=lesson.slug)
