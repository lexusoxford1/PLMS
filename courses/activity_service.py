import logging
import re

from django.utils.html import strip_tags
from django.utils import timezone

from LMS.forms import ActivitySubmissionForm
from LMS.utils import award_course_completion, get_or_create_lesson_progress

from .activity_validation import validate_activity_submission


logger = logging.getLogger("courses.activity_runner")

LANGUAGE_LABELS = {
    "python": "Python",
    "php": "PHP",
    "csharp": "C#",
}

ACTIVITY_CONCEPT_REVIEW_FALLBACKS = {
    "csharp-conditional-statements": {
        "title": "Concept Review",
        "badge": "Unlocked after success",
        "summary": "Conditional logic helps a program choose between different outcomes.",
        "body": (
            "This activity uses an if/else decision. The condition score >= 75 checks whether the learner passed. "
            "If that condition is true, the program prints Passed. Otherwise, the else block runs and prints "
            "Study and try again."
        ),
    }
}


def build_activity_form(lesson, progress):
    rules = lesson.activity_validation_rules or {}
    initial_response = progress.activity_response or rules.get("starter_code", "")
    form = ActivitySubmissionForm(initial={"response": initial_response})
    field = form.fields["response"]

    if lesson.uses_code_runner:
        language = lesson.activity_language
        label = LANGUAGE_LABELS.get(language, "Code")
        field.label = f"{label} code"
        field.help_text = f"Write your {label} solution and submit it to run safely in the lesson code runner."
        field.widget.attrs.update(
            {
                "rows": 18,
                "spellcheck": "false",
                "data-language": language,
                "class": "code-submission-field",
            }
        )
    return form


def build_activity_concept_review(lesson):
    if not lesson or not lesson.has_activity:
        return None

    rules = lesson.activity_validation_rules or {}
    configured_review = rules.get("concept_review")
    if configured_review:
        return {
            "title": configured_review.get("title") or "Concept Review",
            "badge": configured_review.get("badge") or "Unlocked after success",
            "summary": configured_review.get("summary") or "",
            "body": configured_review.get("body") or "",
        }

    fallback = ACTIVITY_CONCEPT_REVIEW_FALLBACKS.get(lesson.slug)
    if fallback:
        return fallback

    return _build_default_concept_review(lesson)


def _build_default_concept_review(lesson):
    summary = (lesson.summary or "").strip()
    lecture_text = _normalize_text(strip_tags(lesson.lecture_content or ""))
    body = _extract_concept_body(lecture_text, summary)

    return {
        "title": "Concept Review",
        "badge": "Unlocked after success",
        "summary": summary or f"Review the main idea behind {lesson.title}.",
        "body": body or "You completed the activity correctly, so this concept review is now unlocked.",
    }


def _extract_concept_body(lecture_text, summary):
    if not lecture_text:
        return ""

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", lecture_text) if part.strip()]
    filtered = [sentence for sentence in sentences if summary.lower() not in sentence.lower()] if summary else sentences
    chosen = filtered[:2] or sentences[:2]
    review = " ".join(chosen).strip()
    if len(review) <= 280:
        return review

    shortened = review[:277].rsplit(" ", 1)[0].strip()
    return f"{shortened}..."


def _normalize_text(value):
    return re.sub(r"\s+", " ", value or "").strip()


def submit_lesson_activity(user, lesson, response):
    progress = get_or_create_lesson_progress(user, lesson)
    progress.activity_response = response
    progress.activity_attempts += 1
    progress.activity_last_submitted_at = timezone.now()

    result = validate_activity_submission(lesson, progress.activity_response)
    progress.activity_completed = result.is_correct
    progress.activity_status = progress.CORRECT if result.is_correct else progress.INCORRECT
    progress.activity_feedback_title = result.title
    progress.activity_feedback_body = result.explanation
    progress.activity_result_data = result.to_payload()
    progress.refresh_completion_state()
    progress.save()

    if result.is_correct and progress.completed_at is not None:
        award_course_completion(user, lesson.course)

    logger.info(
        (
            "activity_submission_evaluated user_id=%s course_id=%s lesson_id=%s "
            "language=%s used_code_runner=%s execution_status=%s validation_result=%s "
            "runtime_available=%s timed_out=%s attempts=%s"
        ),
        user.id,
        lesson.course_id,
        lesson.id,
        result.language or lesson.activity_language,
        result.used_code_runner,
        result.execution_status,
        result.validation_result,
        result.runtime_available,
        result.timed_out,
        progress.activity_attempts,
    )

    return progress, result
