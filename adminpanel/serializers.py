from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from courses.material_library import build_material_view_model


def image_url(field):
    if not field:
        return ""
    try:
        return field.url
    except ValueError:
        return ""


def serialize_course_option(course):
    return {
        "id": course.id,
        "title": course.title,
        "category": course.category,
        "category_label": course.get_category_display(),
    }


def serialize_lesson_option(lesson):
    return {
        "id": lesson.id,
        "title": lesson.title,
        "course_id": lesson.course_id,
        "course_title": lesson.course.title,
        "order": lesson.order,
        "label": f"{lesson.course.title} - Lecture {lesson.order}: {lesson.title}",
    }


def serialize_course(course):
    return {
        "id": course.id,
        "title": course.title,
        "slug": course.slug,
        "description": course.description,
        "category": course.category,
        "category_label": course.get_category_display(),
        "overview": course.overview,
        "difficulty": course.difficulty,
        "difficulty_label": course.get_difficulty_display(),
        "estimated_hours": course.estimated_hours,
        "image_url": image_url(course.image),
        "is_published": course.is_published,
        "created_at": course.created_at.isoformat() if course.created_at else "",
        "updated_at": course.updated_at.isoformat() if course.updated_at else "",
        "enrollment_count": getattr(course, "enrollment_count", None),
        "lesson_count": getattr(course, "lesson_count", None),
        "badge_count": getattr(course, "badge_count", None),
    }


def serialize_lesson(lesson):
    return {
        "id": lesson.id,
        "course_id": lesson.course_id,
        "course_title": lesson.course.title,
        "title": lesson.title,
        "slug": lesson.slug,
        "order": lesson.order,
        "summary": lesson.summary,
        "image_url": image_url(lesson.image),
        "lecture_content": lesson.lecture_content,
        "is_published": lesson.is_published,
        "material_count": getattr(lesson, "material_count", None),
        "has_activity": lesson.has_activity,
        "has_quiz": lesson.has_quiz,
        "updated_at": lesson.updated_at.isoformat() if lesson.updated_at else "",
    }


def serialize_material(material):
    material_view = build_material_view_model(material)
    return {
        "id": material.id,
        "lesson_id": material.lesson_id,
        "lesson_title": material.lesson.title,
        "lesson_order": material.lesson.order,
        "course_id": material.lesson.course_id,
        "course_title": material.lesson.course.title,
        "title": material.title,
        "description": material.description,
        "order": material.order,
        "material_type": material_view["material_type"],
        "material_type_label": material_view["material_type_label"],
        "source_type": material_view["source_type"],
        "source_type_label": material_view["source_type_label"],
        "presentation_provider": material_view["presentation_provider"],
        "presentation_provider_label": material_view["presentation_provider_label"],
        "external_url": material.external_url,
        "file_url": image_url(material.file),
        "source_url": material_view["source_url"],
        "embed_url": material_view["embed_url"],
        "file_name": material_view["file_name"],
        "file_extension": material_view["file_extension"],
        "is_presentation": material_view["is_presentation"],
        "supports_embed": material_view["supports_embed"],
        "viewer_kind": material_view["viewer_kind"],
        "viewer_note": material_view["viewer_note"],
        "uploaded_at": material.uploaded_at.isoformat() if material.uploaded_at else "",
        "updated_at": material.updated_at.isoformat() if material.updated_at else "",
    }


def serialize_choice(choice):
    return {
        "id": choice.id,
        "text": choice.text,
        "is_correct": choice.is_correct,
        "order": choice.order,
    }


def serialize_question(question):
    return {
        "id": question.id,
        "prompt": question.prompt,
        "question_type": question.question_type,
        "question_type_label": question.get_question_type_display(),
        "order": question.order,
        "points": question.points,
        "correct_text": question.correct_text,
        "choices": [serialize_choice(choice) for choice in question.choices.all().order_by("order")],
    }


def serialize_activity_detail(lesson):
    rules = lesson.activity_validation_rules or {}
    try:
        quiz = lesson.quiz
    except ObjectDoesNotExist:
        quiz = None
    return {
        "lesson": serialize_lesson(lesson),
        "activity": {
            "activity_title": lesson.activity_title,
            "activity_instructions": lesson.activity_instructions,
            "activity_hint": lesson.activity_hint,
            "validator_type": rules.get("validator") or ("code_runner" if rules.get("language") else "pattern"),
            "language": rules.get("language", ""),
            "starter_code": rules.get("starter_code", ""),
            "expected_output": rules.get("expected_output", ""),
            "expected_output_contains": rules.get("expected_output_contains", []),
            "output_comparison": rules.get("output_comparison", "exact"),
            "required_patterns": rules.get("required_patterns", []),
            "forbidden_patterns": rules.get("forbidden_patterns", []),
            "success_explanation": rules.get("success_explanation", ""),
            "failure_hint": rules.get("failure_hint", ""),
            "timeout_seconds": rules.get("timeout_seconds", 5),
            "ignore_case": rules.get("ignore_case", False),
            "ignore_whitespace": rules.get("ignore_whitespace", True),
            "min_output_lines": rules.get("min_output_lines", 0),
            "accept_alternative_solutions": rules.get("accept_alternative_solutions", False),
        },
        "quiz": {
            "enabled": bool(quiz),
            "id": quiz.id if quiz else None,
            "title": quiz.title if quiz else "",
            "instructions": quiz.instructions if quiz else "",
            "passing_score": quiz.passing_score if quiz else 70,
            "max_attempts": quiz.max_attempts if quiz else 0,
            "is_published": quiz.is_published if quiz else True,
            "questions": [serialize_question(question) for question in quiz.questions.all().prefetch_related("choices")] if quiz else [],
        },
    }


def serialize_badge(badge):
    return {
        "id": badge.id,
        "name": badge.name,
        "slug": badge.slug,
        "description": badge.description,
        "icon_url": image_url(badge.icon),
        "course_id": badge.course_id,
        "course_title": badge.course.title if badge.course_id else "Platform-wide",
        "award_type": badge.award_type,
        "award_type_label": badge.get_award_type_display(),
        "criteria_key": badge.criteria_key or "",
        "xp_reward": badge.xp_reward,
        "is_active": badge.is_active,
        "award_count": getattr(badge, "award_count", None),
    }


def serialize_user_account(user):
    is_admin = bool(user.is_superuser or user.is_staff or getattr(user, "role", "") == "admin")
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": "admin" if is_admin else "learner",
        "role_label": "Admin" if is_admin else "Learner",
        "is_active": user.is_active,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "date_joined": serialize_recent_timestamp(user.date_joined),
        "last_seen_at": serialize_recent_timestamp(user.last_seen_at),
        "last_login": serialize_recent_timestamp(user.last_login),
        "enrollment_count": getattr(user, "enrollment_count", 0),
        "badge_count": getattr(user, "badge_count", 0),
        "certificate_count": getattr(user, "certificate_count", 0),
    }


def serialize_certificate(certificate):
    return {
        "id": certificate.id,
        "user_id": certificate.user_id,
        "user_name": certificate.user.display_name,
        "user_email": certificate.user.email,
        "course_id": certificate.course_id,
        "course_title": certificate.course.title,
        "badge_name": certificate.badge.name if certificate.badge_id else "",
        "certificate_number": certificate.certificate_number,
        "file_url": image_url(certificate.file),
        "issued_at": certificate.issued_at.isoformat() if certificate.issued_at else "",
        "emailed_at": certificate.emailed_at.isoformat() if certificate.emailed_at else "",
        "created_at": certificate.created_at.isoformat() if certificate.created_at else "",
    }


def serialize_pending_certificate(enrollment):
    return {
        "user_id": enrollment.user_id,
        "user_name": enrollment.user.display_name,
        "user_email": enrollment.user.email,
        "course_id": enrollment.course_id,
        "course_title": enrollment.course.title,
        "completed_at": enrollment.completed_at.isoformat() if enrollment.completed_at else "",
    }


def serialize_recent_timestamp(value):
    if not value:
        return ""
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    return timezone.localtime(value).strftime("%b %d, %Y %I:%M %p")
