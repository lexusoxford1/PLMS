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
            }
            for row in outline
        ],
    }
