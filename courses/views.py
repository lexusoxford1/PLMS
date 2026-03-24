from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from LMS.forms import ActivitySubmissionForm
from LMS.permissions import is_admin_account, learner_required
from LMS.utils import (
    award_course_completion,
    build_course_outline,
    can_access_lesson,
    course_completion_percentage,
    get_or_create_lesson_progress,
)
from badges.models import UserBadge
from badges.services import build_badge_track
from certificates.models import Certificate
from certificates.presentation import build_certificate_preview_model, build_certificate_view_model

from .activity_config import get_effective_activity_rules
from .activity_service import build_activity_concept_review, build_activity_form, build_runner_ui, submit_lesson_activity
from .material_library import build_lesson_material_collections
from .models import Course, Enrollment, Lesson


COURSE_CATALOG_THEMES = {
    "csharp": {
        "language_key": "csharp",
        "language_label": "C#",
        "theme_class": "course-catalog-card--csharp",
        "track_summary": "Object-oriented foundations, problem-solving drills, and app-ready coding habits.",
    },
    "php": {
        "language_key": "php",
        "language_label": "PHP",
        "theme_class": "course-catalog-card--php",
        "track_summary": "Server-side thinking, practical syntax, and web-focused logic building.",
    },
    "python": {
        "language_key": "python",
        "language_label": "Python",
        "theme_class": "course-catalog-card--python",
        "track_summary": "Beginner-friendly automation, clean syntax, and step-by-step programming fluency.",
    },
    "default": {
        "language_key": "general",
        "language_label": "Programming",
        "theme_class": "course-catalog-card--default",
        "track_summary": "Structured lessons with practice checkpoints and guided progression.",
    },
}


def _get_course_catalog_theme(course):
    title = course.title.lower()
    slug = course.slug.lower()
    if "c#" in title or "csharp" in slug:
        return COURSE_CATALOG_THEMES["csharp"]
    if "php" in title or "php" in slug:
        return COURSE_CATALOG_THEMES["php"]
    if "python" in title or "python" in slug:
        return COURSE_CATALOG_THEMES["python"]
    return COURSE_CATALOG_THEMES["default"]


def course_list(request):
    courses = list(Course.objects.filter(is_published=True).prefetch_related("lessons"))
    enrolled_course_ids = set()
    is_admin_viewer = is_admin_account(request.user)
    if request.user.is_authenticated and not is_admin_viewer:
        enrolled_course_ids = set(
            Enrollment.objects.filter(user=request.user, course__in=courses).values_list("course_id", flat=True)
        )

    course_cards = []
    for course in courses:
        published_lessons = [lesson for lesson in course.lessons.all() if lesson.is_published]
        progress_percent = course_completion_percentage(request.user, course)
        is_enrolled = course.id in enrolled_course_ids
        if is_admin_viewer:
            status_label = "Admin view"
            progress_note = "Manage this course from the admin workspace."
            cta_label = "Manage Course"
        elif progress_percent >= 100:
            status_label = "Completed"
            progress_note = "Certificate-ready track"
            cta_label = "Review Course"
        elif is_enrolled and progress_percent > 0:
            status_label = "In Progress"
            progress_note = "Keep your streak moving"
            cta_label = "Continue Course"
        elif is_enrolled:
            status_label = "Enrolled"
            progress_note = "Start your first lesson"
            cta_label = "Start Course"
        elif request.user.is_authenticated:
            status_label = "Available"
            progress_note = "Enroll to track milestones"
            cta_label = "View Course"
        else:
            status_label = "Preview"
            progress_note = "Login to save your progress"
            cta_label = "View Course"

        course_cards.append(
            {
                "course": course,
                "progress_percent": progress_percent,
                "is_enrolled": is_enrolled,
                "lesson_count": len(published_lessons),
                "status_label": status_label,
                "progress_note": progress_note,
                "cta_label": cta_label,
                **_get_course_catalog_theme(course),
            }
        )
    context = {
        "course_cards": course_cards,
        "course_count": len(course_cards),
        "catalog_hours": sum(course.estimated_hours for course in courses),
        "catalog_lessons": sum(card["lesson_count"] for card in course_cards),
        "is_admin_viewer": is_admin_viewer,
    }
    return render(request, "courses/course_list.html", context)


def course_detail(request, slug):
    if is_admin_account(request.user):
        messages.info(request, "Admin accounts manage courses from the Admin Panel instead of learner course pages.")
        if request.user.is_superuser:
            return redirect("adminpanel:courses")
        return redirect("home")

    course = get_object_or_404(Course.objects.prefetch_related("lessons", "badges"), slug=slug, is_published=True)
    enrollment = None
    badge_awards = {}
    certificate = None
    certificate_preview = build_certificate_preview_model(course, request.user if request.user.is_authenticated else None)
    if request.user.is_authenticated:
        enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
        badge_awards = {
            award.badge_id: award
            for award in UserBadge.objects.filter(user=request.user, course=course).select_related("badge", "badge__course")
        }
        certificate = (
            Certificate.objects.filter(user=request.user, course=course)
            .select_related("user", "course", "course__created_by", "badge")
            .first()
        )
        if certificate:
            certificate_preview = build_certificate_view_model(certificate)
    is_enrolled = enrollment is not None
    badge_track = build_badge_track(
        request.user,
        course,
        enrollment=enrollment,
        awards=badge_awards,
    )
    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "outline": build_course_outline(request.user, course),
            "is_enrolled": is_enrolled,
            "badge_track": badge_track,
            "course_xp_total": sum(item["xp_reward"] for item in badge_track),
            "progress_percent": course_completion_percentage(request.user, course),
            "certificate": certificate,
            "certificate_preview": certificate_preview,
        },
    )


@learner_required
def enroll_course(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    enrollment, created = Enrollment.objects.get_or_create(user=request.user, course=course)
    if created:
        messages.success(request, f"You are now enrolled in {course.title}. Your enrollment badge and +40 XP are ready.")
    else:
        messages.info(request, f"You are already enrolled in {course.title}.")
    return redirect("course_detail", slug=course.slug)


@learner_required
def lesson_detail(request, course_slug, lesson_slug):
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    lesson = get_object_or_404(
        Lesson.objects.prefetch_related("materials"),
        course=course,
        slug=lesson_slug,
        is_published=True,
    )

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
    activity_rules = get_effective_activity_rules(lesson)
    material_library = build_lesson_material_collections(lesson, request=request)
    runner_ui = build_runner_ui(lesson)
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
            "activity_rules": activity_rules,
            "activity_concept_review": activity_concept_review,
            "material_library": material_library,
            "runner_ui": runner_ui,
            "next_lesson": next_lesson,
        },
    )


@learner_required
def mark_lecture_complete(request, course_slug, lesson_slug):
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    lesson = get_object_or_404(Lesson, course=course, slug=lesson_slug, is_published=True)
    if request.method == "POST" and can_access_lesson(request.user, lesson):
        progress = get_or_create_lesson_progress(request.user, lesson)
        progress.lecture_completed = True
        progress.refresh_completion_state()
        progress.save()
        if progress.completed_at is not None:
            certificate = award_course_completion(request.user, course)
            if certificate:
                messages.success(request, "Course completed. Your certificate is ready to preview and download.")
                return redirect("certificate_detail", pk=certificate.pk)
        messages.success(request, "Lecture marked as complete.")
    return redirect("lesson_detail", course_slug=course.slug, lesson_slug=lesson.slug)


@learner_required
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
                certificate = Certificate.objects.filter(user=request.user, course=course).first()
                if certificate:
                    messages.success(request, f"{result.title} Your certificate is ready.")
                    return redirect("certificate_detail", pk=certificate.pk)
                messages.success(request, result.title)
            else:
                messages.error(request, result.title)
        else:
            messages.error(request, "Please complete the activity response before submitting.")

    return redirect("lesson_detail", course_slug=course.slug, lesson_slug=lesson.slug)
