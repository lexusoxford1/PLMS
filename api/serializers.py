from LMS.utils import build_course_outline, course_completion_percentage


def serialize_course(course, user=None):
    outline = build_course_outline(user, course) if user is not None else []
    return {
        "id": course.id,
        "title": course.title,
        "slug": course.slug,
        "description": course.description,
        "difficulty": course.difficulty,
        "estimated_hours": course.estimated_hours,
        "progress_percent": course_completion_percentage(user, course) if user is not None else 0,
        "lessons": [
            {
                "id": row["lesson"].id,
                "title": row["lesson"].title,
                "order": row["lesson"].order,
                "accessible": row["accessible"],
                "completed": bool(row["progress"] and row["progress"].completed_at),
                "activity_language": row["lesson"].activity_language,
                "uses_code_runner": row["lesson"].uses_code_runner,
            }
            for row in outline
        ],
    }


def serialize_activity_submission(course, lesson, progress, result):
    next_lesson = course.lessons.filter(is_published=True, order__gt=lesson.order).order_by("order").first()
    notification = result.notification or {
        "level": "success" if result.is_correct else "error",
        "title": result.title,
        "message": result.explanation,
    }
    return {
        "course": {
            "id": course.id,
            "slug": course.slug,
            "title": course.title,
        },
        "lesson": {
            "id": lesson.id,
            "slug": lesson.slug,
            "title": lesson.title,
            "language": lesson.activity_language,
        },
        "activity": result.to_payload(),
        "progress": {
            "lecture_completed": progress.lecture_completed,
            "activity_completed": progress.activity_completed,
            "activity_attempts": progress.activity_attempts,
            "quiz_passed": progress.quiz_passed,
            "lesson_completed": bool(progress.completed_at),
            "next_lesson_unlocked": bool(progress.completed_at),
        },
        "next_lesson": (
            {
                "id": next_lesson.id,
                "slug": next_lesson.slug,
                "title": next_lesson.title,
            }
            if next_lesson and progress.completed_at
            else None
        ),
        "notification": notification,
        "system_notification": notification,
    }
