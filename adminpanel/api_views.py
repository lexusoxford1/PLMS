import json
from collections import defaultdict
from datetime import timedelta
from functools import wraps

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from LMS.permissions import admin_account_q, learner_account_q
from LMS.utils import award_course_completion
from badges.models import Badge, UserBadge
from certificates.models import Certificate
from courses.models import Course, Enrollment, LearningMaterial, Lesson
from progress.models import LessonProgress
from quizzes.models import Choice, Question, Quiz

from .forms import BadgeAdminForm, CourseAdminForm, LearningMaterialAdminForm, LessonAdminForm, UserRoleAdminForm
from .mixins import ADMIN_PANEL_ACCESS_DENIED_MESSAGE, can_access_admin_panel
from .serializers import (
    serialize_activity_detail,
    serialize_badge,
    serialize_certificate,
    serialize_course,
    serialize_course_option,
    serialize_lesson,
    serialize_lesson_option,
    serialize_material,
    serialize_pending_certificate,
    serialize_recent_timestamp,
    serialize_user_account,
)


User = get_user_model()


def admin_api_view(view_func):
    login_gate = login_required(view_func, login_url="adminpanel:login")

    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "detail": "Authentication required.",
                        "login_url": reverse("adminpanel:login"),
                    },
                    status=401,
                )
            return login_gate(request, *args, **kwargs)
        if not can_access_admin_panel(request.user):
            return JsonResponse({"detail": ADMIN_PANEL_ACCESS_DENIED_MESSAGE}, status=403)
        return view_func(request, *args, **kwargs)

    return wrapped


def form_error_response(form, *, status=400):
    errors = {
        field: [item["message"] for item in details]
        for field, details in form.errors.get_json_data().items()
    }
    return JsonResponse({"errors": errors}, status=status)


def payload_error(errors, *, status=400):
    return JsonResponse({"errors": errors}, status=status)


def parse_json_request(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}"), None
    except json.JSONDecodeError:
        return None, payload_error({"__all__": ["Invalid JSON payload."]})


def safe_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def serialize_category_options():
    return [{"id": value, "title": label} for value, label in Course.CATEGORY_CHOICES]


def user_accounts_queryset():
    return User.objects.annotate(
        enrollment_count=Count("enrollments", distinct=True),
        badge_count=Count("user_badges", distinct=True),
        certificate_count=Count("certificates", distinct=True),
    ).order_by("-is_superuser", "-is_staff", "username")


def normalize_rule_entries(items, *, label):
    errors = []
    normalized = []
    if items in (None, ""):
        return normalized, errors
    if not isinstance(items, list):
        return normalized, [f"{label} must be a list."]

    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            errors.append(f"{label} rule #{index} must be an object.")
            continue
        pattern = str(item.get("pattern") or "").strip()
        if not pattern:
            continue
        count = safe_int(item.get("count"), 1)
        if count is None or count < 1:
            errors.append(f"{label} rule #{index} must use a count of at least 1.")
            count = 1
        normalized.append(
            {
                "pattern": pattern,
                "description": str(item.get("description") or pattern).strip(),
                "count": count,
                "case_sensitive": bool(item.get("case_sensitive")),
            }
        )
    return normalized, errors


def build_activity_rules(payload):
    errors = {}

    activity_title = str(payload.get("activity_title") or "").strip()
    activity_instructions = str(payload.get("activity_instructions") or "").strip()
    activity_hint = str(payload.get("activity_hint") or "").strip()
    validator_type = str(payload.get("validator_type") or "").strip() or "pattern"

    required_patterns, required_errors = normalize_rule_entries(
        payload.get("required_patterns"),
        label="Required pattern",
    )
    forbidden_patterns, forbidden_errors = normalize_rule_entries(
        payload.get("forbidden_patterns"),
        label="Forbidden pattern",
    )
    if required_errors:
        errors["required_patterns"] = required_errors
    if forbidden_errors:
        errors["forbidden_patterns"] = forbidden_errors

    has_activity_content = bool(activity_title or activity_instructions or activity_hint)
    has_validation_config = bool(
        required_patterns
        or forbidden_patterns
        or payload.get("language")
        or payload.get("expected_output")
        or payload.get("expected_output_contains")
    )

    if not has_activity_content and not has_validation_config:
        return {
            "activity_title": "",
            "activity_instructions": "",
            "activity_hint": "",
            "activity_validation_rules": {},
        }, errors

    if not activity_instructions:
        errors.setdefault("activity_instructions", []).append("Activity instructions are required.")

    if validator_type == "code_runner":
        language = str(payload.get("language") or "").strip().lower()
        if language not in {Course.CATEGORY_CSHARP, Course.CATEGORY_PYTHON, Course.CATEGORY_PHP}:
            errors.setdefault("language", []).append("Select a supported programming language.")

        expected_output = str(payload.get("expected_output") or "").strip()
        expected_output_contains = payload.get("expected_output_contains") or []
        if not isinstance(expected_output_contains, list):
            errors.setdefault("expected_output_contains", []).append("Expected output contains must be a list.")
            expected_output_contains = []
        expected_output_contains = [str(item).strip() for item in expected_output_contains if str(item).strip()]
        if not expected_output and not expected_output_contains:
            errors.setdefault("expected_output", []).append(
                "Add exact expected output or at least one contains check."
            )

        rules = {
            "validator": "code_runner",
            "language": language,
            "starter_code": str(payload.get("starter_code") or ""),
            "expected_output": expected_output,
            "expected_output_contains": expected_output_contains,
            "output_comparison": str(payload.get("output_comparison") or "exact"),
            "required_patterns": required_patterns,
            "forbidden_patterns": forbidden_patterns,
            "success_explanation": str(payload.get("success_explanation") or "").strip(),
            "failure_hint": str(payload.get("failure_hint") or "").strip(),
            "timeout_seconds": safe_int(payload.get("timeout_seconds"), 5) or 5,
            "ignore_case": bool(payload.get("ignore_case")),
            "ignore_whitespace": bool(payload.get("ignore_whitespace", True)),
            "min_output_lines": max(0, safe_int(payload.get("min_output_lines"), 0) or 0),
            "accept_alternative_solutions": bool(payload.get("accept_alternative_solutions")),
        }
    else:
        if not required_patterns and not forbidden_patterns:
            errors.setdefault("required_patterns", []).append("Add at least one validation rule for the activity.")
        rules = {
            "required_patterns": required_patterns,
            "forbidden_patterns": forbidden_patterns,
            "success_explanation": str(payload.get("success_explanation") or "").strip(),
            "failure_hint": str(payload.get("failure_hint") or "").strip(),
        }

    return {
        "activity_title": activity_title,
        "activity_instructions": activity_instructions,
        "activity_hint": activity_hint,
        "activity_validation_rules": rules,
    }, errors


def validate_quiz_payload(quiz_payload):
    errors = {}
    enabled = bool(quiz_payload.get("enabled"))
    if not enabled:
        return {"enabled": False, "questions": []}, errors

    title = str(quiz_payload.get("title") or "").strip()
    instructions = str(quiz_payload.get("instructions") or "").strip()
    passing_score = safe_int(quiz_payload.get("passing_score"), 70)
    max_attempts = safe_int(quiz_payload.get("max_attempts"), 0)
    is_published = bool(quiz_payload.get("is_published", True))
    questions_payload = quiz_payload.get("questions") or []

    if not title:
        errors.setdefault("quiz.title", []).append("Quiz title is required.")
    if passing_score is None or passing_score < 1 or passing_score > 100:
        errors.setdefault("quiz.passing_score", []).append("Passing score must be between 1 and 100.")
    if max_attempts is None or max_attempts < 0:
        errors.setdefault("quiz.max_attempts", []).append("Max attempts must be zero or greater.")
    if not isinstance(questions_payload, list) or not questions_payload:
        errors.setdefault("quiz.questions", []).append("Add at least one quiz question.")
        questions_payload = []

    normalized_questions = []
    for index, item in enumerate(questions_payload, start=1):
        prefix = f"quiz.questions[{index}]"
        if not isinstance(item, dict):
            errors.setdefault(prefix, []).append("Question payload must be an object.")
            continue

        prompt = str(item.get("prompt") or "").strip()
        question_type = str(item.get("question_type") or Question.MULTIPLE_CHOICE).strip()
        points = safe_int(item.get("points"), 1)
        correct_text = str(item.get("correct_text") or "").strip()

        if not prompt:
            errors.setdefault(f"{prefix}.prompt", []).append("Question text is required.")
        if question_type not in {Question.MULTIPLE_CHOICE, Question.SHORT_TEXT}:
            errors.setdefault(f"{prefix}.question_type", []).append("Select a supported question type.")
        if points is None or points < 1:
            errors.setdefault(f"{prefix}.points", []).append("Points must be at least 1.")

        normalized_choices = []
        if question_type == Question.MULTIPLE_CHOICE:
            choices = item.get("choices") or []
            if not isinstance(choices, list):
                errors.setdefault(f"{prefix}.choices", []).append("Choices must be a list.")
                choices = []
            correct_count = 0
            for choice_index, choice in enumerate(choices, start=1):
                if not isinstance(choice, dict):
                    errors.setdefault(f"{prefix}.choices[{choice_index}]", []).append("Choice payload must be an object.")
                    continue
                text = str(choice.get("text") or "").strip()
                if not text:
                    continue
                is_correct = bool(choice.get("is_correct"))
                if is_correct:
                    correct_count += 1
                normalized_choices.append(
                    {
                        "id": safe_int(choice.get("id")),
                        "text": text,
                        "is_correct": is_correct,
                    }
                )
            if len(normalized_choices) < 2:
                errors.setdefault(f"{prefix}.choices", []).append(
                    "Multiple-choice questions need at least two non-empty choices."
                )
            if correct_count != 1:
                errors.setdefault(f"{prefix}.choices", []).append(
                    "Multiple-choice questions need exactly one correct choice."
                )
        else:
            if not correct_text:
                errors.setdefault(f"{prefix}.correct_text", []).append(
                    "Short-answer questions need a correct answer."
                )

        normalized_questions.append(
            {
                "id": safe_int(item.get("id")),
                "prompt": prompt,
                "question_type": question_type,
                "points": points or 1,
                "correct_text": correct_text,
                "choices": normalized_choices,
            }
        )

    return {
        "enabled": True,
        "title": title,
        "instructions": instructions,
        "passing_score": passing_score,
        "max_attempts": max_attempts,
        "is_published": is_published,
        "questions": normalized_questions,
    }, errors


def sync_lesson_progress_requirements(lesson, *, had_activity, had_quiz):
    has_activity = lesson.has_activity
    has_quiz = Quiz.objects.filter(lesson=lesson).exists()

    for progress in lesson.progress_records.all():
        if not has_activity:
            progress.activity_completed = True
        elif not had_activity and has_activity:
            progress.activity_completed = False
            progress.activity_status = progress.PENDING

        if not has_quiz:
            progress.quiz_passed = True
        elif not had_quiz and has_quiz:
            progress.quiz_passed = False

        progress.refresh_completion_state()
        progress.save()


def save_quiz_configuration(lesson, quiz_payload):
    config, errors = validate_quiz_payload(quiz_payload)
    if errors:
        return None, errors

    quiz = Quiz.objects.filter(lesson=lesson).first()
    if not config["enabled"]:
        if quiz:
            quiz.delete()
        return None, {}

    quiz, _ = Quiz.objects.update_or_create(
        lesson=lesson,
        defaults={
            "title": config["title"],
            "instructions": config["instructions"],
            "passing_score": config["passing_score"],
            "max_attempts": config["max_attempts"],
            "is_published": config["is_published"],
        },
    )

    kept_question_ids = []
    for order, question_data in enumerate(config["questions"], start=1):
        question = quiz.questions.filter(pk=question_data["id"]).first() if question_data["id"] else None
        if question is None:
            question = Question(quiz=quiz)
        question.prompt = question_data["prompt"]
        question.question_type = question_data["question_type"]
        question.order = order
        question.points = question_data["points"]
        question.correct_text = question_data["correct_text"] if question.question_type == Question.SHORT_TEXT else ""
        question.save()
        kept_question_ids.append(question.id)

        if question.question_type == Question.SHORT_TEXT:
            question.choices.all().delete()
            continue

        kept_choice_ids = []
        for choice_order, choice_data in enumerate(question_data["choices"], start=1):
            choice = question.choices.filter(pk=choice_data["id"]).first() if choice_data["id"] else None
            if choice is None:
                choice = Choice(question=question)
            choice.text = choice_data["text"]
            choice.is_correct = choice_data["is_correct"]
            choice.order = choice_order
            choice.save()
            kept_choice_ids.append(choice.id)
        question.choices.exclude(id__in=kept_choice_ids).delete()

    quiz.questions.exclude(id__in=kept_question_ids).delete()
    return quiz, {}


@admin_api_view
@require_GET
def lookups(request):
    course_id = request.GET.get("course")
    courses = Course.objects.order_by("title")
    lectures = Lesson.objects.select_related("course").order_by("course__title", "order")
    if course_id:
        lectures = lectures.filter(course_id=course_id)
    return JsonResponse(
        {
            "courses": [serialize_course_option(course) for course in courses],
            "lectures": [serialize_lesson_option(lesson) for lesson in lectures],
        }
    )


@admin_api_view
@require_GET
def dashboard(request):
    now = timezone.now()
    online_since = now - timedelta(minutes=5)
    active_since = now - timedelta(hours=24)

    course_rows = Course.objects.annotate(
        enrollment_count=Count("enrollments", filter=learner_account_q("enrollments__user__"), distinct=True),
        lesson_count=Count("lessons", distinct=True),
        badge_count=Count("badges", distinct=True),
    ).order_by("-enrollment_count", "title")

    total_enrollments = Enrollment.objects.filter(learner_account_q("user__")).count()
    completed_enrollments = Enrollment.objects.filter(learner_account_q("user__"), completed_at__isnull=False).count()
    recent_enrollments = (
        Enrollment.objects.select_related("user", "course").filter(learner_account_q("user__")).order_by("-enrolled_at")[:6]
    )
    recent_badges = (
        UserBadge.objects.select_related("user", "badge", "course").filter(learner_account_q("user__")).order_by("-awarded_at")[:6]
    )
    recent_certificates = (
        Certificate.objects.select_related("user", "course", "badge")
        .filter(learner_account_q("user__"))
        .order_by("-created_at")[:6]
    )

    payload = {
        "metrics": {
            "total_users": User.objects.count(),
            "active_users": User.objects.filter(
                Q(last_seen_at__gte=active_since) | Q(last_login__gte=active_since)
            ).count(),
            "online_users": User.objects.filter(last_seen_at__gte=online_since).count(),
            "total_courses": Course.objects.count(),
            "total_enrollments": total_enrollments,
            "completion_rate": int((completed_enrollments / total_enrollments) * 100) if total_enrollments else 0,
        },
        "course_cards": [serialize_course(course) for course in course_rows],
        "recent_activity": {
            "enrollments": [
                {
                    "user_name": enrollment.user.display_name,
                    "course_title": enrollment.course.title,
                    "timestamp": serialize_recent_timestamp(enrollment.enrolled_at),
                }
                for enrollment in recent_enrollments
            ],
            "badges": [
                {
                    "user_name": award.user.display_name,
                    "badge_name": award.badge.name,
                    "course_title": award.course.title if award.course_id else "Platform",
                    "timestamp": serialize_recent_timestamp(award.awarded_at),
                }
                for award in recent_badges
            ],
            "certificates": [
                {
                    "user_name": certificate.user.display_name,
                    "course_title": certificate.course.title,
                    "timestamp": serialize_recent_timestamp(certificate.created_at),
                }
                for certificate in recent_certificates
            ],
        },
    }
    return JsonResponse(payload)


@admin_api_view
@require_http_methods(["GET", "POST"])
def courses_collection(request):
    if request.method == "GET":
        category = (request.GET.get("category") or "").strip()
        courses = Course.objects.order_by("title")
        if category:
            courses = courses.filter(category=category)
        if request.GET.get("compact"):
            return JsonResponse({"items": [serialize_course_option(course) for course in courses], "categories": serialize_category_options()})

        courses = courses.annotate(
            enrollment_count=Count("enrollments", filter=learner_account_q("enrollments__user__"), distinct=True),
            lesson_count=Count("lessons", distinct=True),
            badge_count=Count("badges", distinct=True),
        )
        return JsonResponse({"items": [serialize_course(course) for course in courses], "categories": serialize_category_options()})

    form = CourseAdminForm(request.POST, request.FILES)
    if not form.is_valid():
        return form_error_response(form)
    course = form.save(commit=False)
    if not course.created_by_id:
        course.created_by = request.user
    course.save()
    return JsonResponse({"item": serialize_course(course), "message": "Course created successfully."}, status=201)


@admin_api_view
@require_http_methods(["GET", "POST", "DELETE"])
def course_detail(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    if request.method == "GET":
        course.enrollment_count = course.enrollments.filter(learner_account_q("user__")).count()
        course.lesson_count = course.lessons.count()
        course.badge_count = course.badges.count()
        lessons = course.lessons.select_related("course").annotate(material_count=Count("materials", distinct=True))
        return JsonResponse(
            {
                "item": serialize_course(course),
                "lectures": [serialize_lesson(lesson) for lesson in lessons.order_by("order")],
            }
        )

    if request.method == "DELETE":
        course.delete()
        return JsonResponse({"message": "Course deleted successfully."})

    form = CourseAdminForm(request.POST, request.FILES, instance=course)
    if not form.is_valid():
        return form_error_response(form)
    course = form.save()
    course.enrollment_count = course.enrollments.filter(learner_account_q("user__")).count()
    course.lesson_count = course.lessons.count()
    course.badge_count = course.badges.count()
    return JsonResponse({"item": serialize_course(course), "message": "Course updated successfully."})


@admin_api_view
@require_http_methods(["GET", "POST"])
def lectures_collection(request):
    course_id = request.GET.get("course")
    lectures = Lesson.objects.select_related("course").annotate(material_count=Count("materials", distinct=True))
    if course_id:
        lectures = lectures.filter(course_id=course_id)
    lectures = lectures.order_by("course__title", "order")

    if request.method == "GET":
        if request.GET.get("compact"):
            return JsonResponse({"items": [serialize_lesson_option(lesson) for lesson in lectures]})
        return JsonResponse({"items": [serialize_lesson(lesson) for lesson in lectures]})

    form = LessonAdminForm(request.POST, request.FILES)
    if not form.is_valid():
        return form_error_response(form)
    lesson = form.save()
    lesson.material_count = lesson.materials.count()
    return JsonResponse({"item": serialize_lesson(lesson), "message": "Lecture created successfully."}, status=201)


@admin_api_view
@require_http_methods(["GET", "POST", "DELETE"])
def lecture_detail(request, lecture_id):
    lesson = get_object_or_404(Lesson.objects.select_related("course"), pk=lecture_id)

    if request.method == "GET":
        lesson.material_count = lesson.materials.count()
        materials = lesson.materials.select_related("lesson__course").order_by("order", "title")
        return JsonResponse(
            {
                "item": serialize_lesson(lesson),
                "materials": [serialize_material(material) for material in materials],
            }
        )

    if request.method == "DELETE":
        lesson.delete()
        return JsonResponse({"message": "Lecture deleted successfully."})

    form = LessonAdminForm(request.POST, request.FILES, instance=lesson)
    if not form.is_valid():
        return form_error_response(form)
    lesson = form.save()
    lesson.material_count = lesson.materials.count()
    return JsonResponse({"item": serialize_lesson(lesson), "message": "Lecture updated successfully."})


@admin_api_view
@require_http_methods(["GET", "POST"])
def materials_collection(request):
    lesson_id = request.GET.get("lecture")
    course_id = request.GET.get("course")
    materials = LearningMaterial.objects.select_related("lesson", "lesson__course").order_by(
        "lesson__course__title",
        "lesson__order",
        "order",
        "title",
    )
    if lesson_id:
        materials = materials.filter(lesson_id=lesson_id)
    if course_id:
        materials = materials.filter(lesson__course_id=course_id)

    if request.method == "GET":
        return JsonResponse({"items": [serialize_material(material) for material in materials]})

    form = LearningMaterialAdminForm(request.POST, request.FILES)
    if not form.is_valid():
        return form_error_response(form)
    material = form.save()
    return JsonResponse({"item": serialize_material(material), "message": "Material uploaded successfully."}, status=201)


@admin_api_view
@require_http_methods(["GET", "POST", "DELETE"])
def material_detail(request, material_id):
    material = get_object_or_404(LearningMaterial.objects.select_related("lesson", "lesson__course"), pk=material_id)

    if request.method == "GET":
        return JsonResponse({"item": serialize_material(material)})

    if request.method == "DELETE":
        material.delete()
        return JsonResponse({"message": "Material deleted successfully."})

    form = LearningMaterialAdminForm(request.POST, request.FILES, instance=material)
    if not form.is_valid():
        return form_error_response(form)
    material = form.save()
    return JsonResponse({"item": serialize_material(material), "message": "Material updated successfully."})


@admin_api_view
@require_GET
def activities_collection(request):
    course_id = request.GET.get("course")
    lessons = Lesson.objects.select_related("course").annotate(question_count=Count("quiz__questions", distinct=True))
    if course_id:
        lessons = lessons.filter(course_id=course_id)
    lessons = lessons.order_by("course__title", "order")

    items = []
    for lesson in lessons:
        rules = lesson.activity_validation_rules or {}
        quiz = Quiz.objects.filter(lesson=lesson).first()
        items.append(
            {
                "id": lesson.id,
                "title": lesson.title,
                "course_id": lesson.course_id,
                "course_title": lesson.course.title,
                "order": lesson.order,
                "has_activity": lesson.has_activity,
                "validator_type": rules.get("validator") or ("code_runner" if rules.get("language") else "pattern"),
                "language": rules.get("language", ""),
                "has_quiz": quiz is not None,
                "question_count": lesson.question_count,
                "passing_score": quiz.passing_score if quiz else None,
            }
        )
    return JsonResponse({"items": items})


@admin_api_view
@require_http_methods(["GET", "POST"])
@transaction.atomic
def activity_detail(request, lecture_id):
    lesson = get_object_or_404(
        Lesson.objects.select_related("course").prefetch_related("quiz__questions__choices"),
        pk=lecture_id,
    )

    if request.method == "GET":
        return JsonResponse({"item": serialize_activity_detail(lesson)})

    payload, error_response = parse_json_request(request)
    if error_response:
        return error_response

    activity_config, activity_errors = build_activity_rules(payload)
    quiz_payload = payload.get("quiz") or {}
    _, quiz_errors = validate_quiz_payload(quiz_payload)
    errors = {**activity_errors, **quiz_errors}
    if errors:
        return payload_error(errors)

    had_activity = lesson.has_activity
    had_quiz = Quiz.objects.filter(lesson=lesson).exists()

    lesson.activity_title = activity_config["activity_title"]
    lesson.activity_instructions = activity_config["activity_instructions"]
    lesson.activity_hint = activity_config["activity_hint"]
    lesson.activity_validation_rules = activity_config["activity_validation_rules"]
    lesson.save(
        update_fields=[
            "activity_title",
            "activity_instructions",
            "activity_hint",
            "activity_validation_rules",
            "updated_at",
        ]
    )

    _, quiz_errors = save_quiz_configuration(lesson, quiz_payload)
    if quiz_errors:
        transaction.set_rollback(True)
        return payload_error(quiz_errors)

    sync_lesson_progress_requirements(lesson, had_activity=had_activity, had_quiz=had_quiz)

    lesson = Lesson.objects.select_related("course").prefetch_related("quiz__questions__choices").get(pk=lesson.pk)
    return JsonResponse({"item": serialize_activity_detail(lesson), "message": "Activity settings updated successfully."})


@admin_api_view
@require_GET
def progress_overview(request):
    course_id = request.GET.get("course")
    enrollments = list(
        Enrollment.objects.select_related("user", "course").filter(learner_account_q("user__")).order_by("-enrolled_at")
    )
    if course_id:
        enrollments = [enrollment for enrollment in enrollments if str(enrollment.course_id) == str(course_id)]

    course_ids = sorted({enrollment.course_id for enrollment in enrollments})
    courses = list(Course.objects.filter(id__in=course_ids).prefetch_related("lessons").order_by("title"))

    lesson_totals = {}
    activity_totals = {}
    quiz_totals = {}
    for course in courses:
        lessons = [lesson for lesson in course.lessons.all() if lesson.is_published]
        lesson_totals[course.id] = len(lessons)
        activity_totals[course.id] = sum(1 for lesson in lessons if lesson.has_activity)
        quiz_totals[course.id] = sum(1 for lesson in lessons if lesson.has_quiz)

    progress_records = list(
        LessonProgress.objects.select_related("lesson__course", "user").filter(lesson__course_id__in=course_ids)
    )
    progress_by_pair = defaultdict(list)
    for progress in progress_records:
        progress_by_pair[(progress.user_id, progress.lesson.course_id)].append(progress)

    items = []
    completed_enrollments = 0
    for enrollment in enrollments:
        totals = lesson_totals.get(enrollment.course_id, 0)
        records = progress_by_pair.get((enrollment.user_id, enrollment.course_id), [])
        completed_lessons = sum(1 for progress in records if progress.completed_at is not None)
        activities_completed = sum(1 for progress in records if progress.activity_completed and progress.lesson.has_activity)
        quizzes_passed = sum(1 for progress in records if progress.quiz_passed and progress.lesson.has_quiz)
        if enrollment.completed_at:
            completed_enrollments += 1

        items.append(
            {
                "user_name": enrollment.user.display_name,
                "user_email": enrollment.user.email,
                "course_title": enrollment.course.title,
                "course_id": enrollment.course_id,
                "progress_percent": int((completed_lessons / totals) * 100) if totals else 0,
                "completed_lessons": completed_lessons,
                "total_lessons": totals,
                "completed_activities": activities_completed,
                "total_activities": activity_totals.get(enrollment.course_id, 0),
                "passed_quizzes": quizzes_passed,
                "total_quizzes": quiz_totals.get(enrollment.course_id, 0),
                "enrolled_at": serialize_recent_timestamp(enrollment.enrolled_at),
                "completed_at": serialize_recent_timestamp(enrollment.completed_at),
                "status": "Completed" if enrollment.completed_at else "In Progress",
            }
        )

    total_enrollments = len(enrollments)
    return JsonResponse(
        {
            "courses": [serialize_course_option(course) for course in Course.objects.order_by("title")],
            "summary": {
                "total_enrollments": total_enrollments,
                "completed_enrollments": completed_enrollments,
                "completion_rate": int((completed_enrollments / total_enrollments) * 100) if total_enrollments else 0,
                "active_courses": len(course_ids),
            },
            "items": items,
        }
    )


@admin_api_view
@require_http_methods(["GET", "POST"])
def badges_collection(request):
    if request.method == "GET":
        badges = Badge.objects.select_related("course").annotate(
            award_count=Count("awards", filter=learner_account_q("awards__user__"), distinct=True)
        ).order_by(
            "course__title",
            "award_type",
            "name",
        )
        return JsonResponse({"items": [serialize_badge(badge) for badge in badges]})

    form = BadgeAdminForm(request.POST, request.FILES)
    if not form.is_valid():
        return form_error_response(form)
    badge = form.save()
    badge.award_count = badge.awards.filter(learner_account_q("user__")).count()
    return JsonResponse({"item": serialize_badge(badge), "message": "Badge created successfully."}, status=201)


@admin_api_view
@require_http_methods(["GET", "POST", "DELETE"])
def badge_detail(request, badge_id):
    badge = get_object_or_404(Badge.objects.select_related("course"), pk=badge_id)

    if request.method == "GET":
        badge.award_count = badge.awards.filter(learner_account_q("user__")).count()
        return JsonResponse({"item": serialize_badge(badge)})

    if request.method == "DELETE":
        badge.delete()
        return JsonResponse({"message": "Badge deleted successfully."})

    form = BadgeAdminForm(request.POST, request.FILES, instance=badge)
    if not form.is_valid():
        return form_error_response(form)
    badge = form.save()
    badge.award_count = badge.awards.filter(learner_account_q("user__")).count()
    return JsonResponse({"item": serialize_badge(badge), "message": "Badge updated successfully."})


@admin_api_view
@require_GET
def users_collection(request):
    role_filter = request.GET.get("role")
    users = user_accounts_queryset()
    if role_filter == getattr(User, "ADMIN", "admin"):
        users = users.filter(admin_account_q())
    elif role_filter == getattr(User, "LEARNER", "learner"):
        users = users.filter(learner_account_q())

    online_since = timezone.now() - timedelta(minutes=5)
    return JsonResponse(
        {
            "summary": {
                "total_accounts": User.objects.count(),
                "active_accounts": User.objects.filter(is_active=True).count(),
                "admin_accounts": User.objects.filter(admin_account_q()).count(),
                "learner_accounts": User.objects.filter(learner_account_q()).count(),
                "online_accounts": User.objects.filter(is_active=True, last_seen_at__gte=online_since).count(),
            },
            "items": [serialize_user_account(user) for user in users],
        }
    )


@admin_api_view
@require_http_methods(["GET", "POST"])
def user_detail(request, user_id):
    user = get_object_or_404(user_accounts_queryset(), pk=user_id)

    if request.method == "GET":
        return JsonResponse({"item": serialize_user_account(user)})

    payload, error_response = parse_json_request(request)
    if error_response:
        return error_response

    form = UserRoleAdminForm(payload, instance=user)
    if not form.is_valid():
        return form_error_response(form)

    desired_role = form.cleaned_data["role"]
    desired_active = form.cleaned_data["is_active"]
    is_current_admin = bool(user.is_superuser or user.is_staff or user.role == getattr(User, "ADMIN", "admin"))
    last_other_superuser_exists = User.objects.filter(is_superuser=True, is_active=True).exclude(pk=user.pk).exists()

    if user.pk == request.user.pk:
        if desired_role != getattr(User, "ADMIN", "admin"):
            return payload_error({"role": ["You cannot remove your own admin access from the Admin Panel."]})
        if not desired_active:
            return payload_error({"is_active": ["You cannot deactivate your own superuser account."]})

    if is_current_admin and (desired_role != getattr(User, "ADMIN", "admin") or not desired_active) and not last_other_superuser_exists:
        return payload_error({"role": ["Keep at least one active superuser account for the Admin Panel."]})

    user = form.save(commit=False)
    if desired_role == getattr(User, "ADMIN", "admin"):
        user.role = getattr(User, "ADMIN", "admin")
        user.is_staff = True
        user.is_superuser = True
    else:
        user.role = getattr(User, "LEARNER", "learner")
        user.is_staff = False
        user.is_superuser = False
    user.is_active = desired_active
    user.save()
    user = user_accounts_queryset().get(pk=user.pk)
    return JsonResponse({"item": serialize_user_account(user), "message": "User account updated successfully."})


@admin_api_view
@require_GET
def certificates_overview(request):
    certificates = list(
        Certificate.objects.select_related("user", "course", "badge")
        .filter(learner_account_q("user__"))
        .order_by("-issued_at", "-created_at")
    )
    existing_pairs = {(certificate.user_id, certificate.course_id) for certificate in certificates}
    pending = [
        enrollment
        for enrollment in Enrollment.objects.select_related("user", "course")
        .filter(learner_account_q("user__"), completed_at__isnull=False)
        .order_by("-completed_at")
        if (enrollment.user_id, enrollment.course_id) not in existing_pairs
    ]

    return JsonResponse(
        {
            "summary": {
                "issued_count": len(certificates),
                "pending_count": len(pending),
            },
            "items": [serialize_certificate(certificate) for certificate in certificates],
            "pending": [serialize_pending_certificate(enrollment) for enrollment in pending],
        }
    )


@admin_api_view
@require_http_methods(["POST"])
def certificate_issue(request):
    payload, error_response = parse_json_request(request)
    if error_response:
        return error_response

    user_id = payload.get("user_id")
    course_id = payload.get("course_id")
    if not user_id or not course_id:
        return payload_error({"__all__": ["User and course are required to issue a certificate."]})

    user = get_object_or_404(User, pk=user_id)
    course = get_object_or_404(Course, pk=course_id)
    certificate = award_course_completion(user, course)
    if certificate is None:
        return payload_error(
            {"__all__": ["This learner has not completed the course requirements yet."]},
            status=400,
        )

    certificate = Certificate.objects.select_related("user", "course", "badge").get(pk=certificate.pk)
    return JsonResponse({"item": serialize_certificate(certificate), "message": "Certificate issued successfully."})


@admin_api_view
@require_http_methods(["POST"])
def certificate_refresh(request, certificate_id):
    certificate = get_object_or_404(Certificate.objects.select_related("user", "course", "badge"), pk=certificate_id)
    certificate.refresh_artifact()
    certificate.refresh_from_db()
    return JsonResponse({"item": serialize_certificate(certificate), "message": "Certificate refreshed successfully."})


@admin_api_view
@require_http_methods(["POST"])
def certificate_email(request, certificate_id):
    certificate = get_object_or_404(Certificate.objects.select_related("user", "course", "badge"), pk=certificate_id)
    certificate.refresh_artifact()
    sent = certificate.send_via_email()
    certificate.refresh_from_db()
    if not sent:
        return payload_error(
            {"__all__": ["The certificate could not be emailed because the learner does not have a valid email or file."]},
            status=400,
        )
    return JsonResponse({"item": serialize_certificate(certificate), "message": "Certificate emailed successfully."})
