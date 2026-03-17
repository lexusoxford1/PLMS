import logging
import re

from django.utils.html import strip_tags
from django.utils import timezone

from LMS.forms import ActivitySubmissionForm
from LMS.utils import award_course_completion, get_or_create_lesson_progress

from .activity_config import get_effective_activity_language, get_effective_activity_rules, uses_effective_code_runner
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

DEDICATED_CODE_RUNNER_LANGUAGES = {"csharp", "python", "php"}

CODE_RUNNER_UI = {
    "csharp": {
        "headline": "Dedicated C# Compiler",
        "workspace_default_title": "C# Compiler Lab",
        "workspace_body": (
            "Work through the task in one place, then compile safely with the lesson runner. "
            "You will see friendly guidance, exact compiler feedback, and your program output below the editor."
        ),
        "file_name": "Program.cs",
        "tool_label": ".NET / C#",
        "feedback_label": "Backend popup",
        "lesson_badge": "C# lesson",
        "quick_start_steps": [
            "Read the task and keep your solution inside Main().",
            "Use Run Code after small changes so errors are easier to fix.",
            "Review compiler notes, output, and hints in the panel below the editor.",
        ],
        "note_chips": [
            "Program.cs is the active file",
            "Balanced braces matter",
            "Run often, fix one issue at a time",
        ],
        "hint_default": "Compile the code and read the backend compiler feedback carefully.",
        "tool_tab_label": "Run Code",
        "default_notification_title": "C# compiler feedback will appear here.",
        "default_notification_message": (
            "Use Run Code to compile and execute the current C# program. The backend compiler service "
            "will update this panel with the result."
        ),
        "default_notification_label": "Compiler feedback",
        "results_heading": "Run Results",
        "editor_tip_primary": "Tip: keep Main() as your entry point.",
        "editor_tip_secondary": "Backend notifications and execution output stay inside this panel.",
        "submit_idle_label": "Run Code",
        "submit_busy_label": "Compiling...",
        "action_meta": "Backend-driven compiler feedback in this panel",
        "default_error_title": "Compiler Details",
        "environment_error_title": "Compiler Environment Details",
        "runtime_error_kind": "csharp_runtime_error",
        "detail_caption": "Compiler service output",
        "environment_detail_caption": "Compiler environment output",
    },
    "python": {
        "headline": "Dedicated Python Compiler",
        "workspace_default_title": "Python Compiler Lab",
        "workspace_body": (
            "Work through the task in one place, then write, run, and test your Python code safely inside the lesson workspace. "
            "You will see friendly guidance, backend feedback, and your program output below the editor."
        ),
        "file_name": "main.py",
        "tool_label": "Python runtime",
        "feedback_label": "Backend popup",
        "lesson_badge": "Python lesson",
        "quick_start_steps": [
            "Read the task and keep your solution inside main.py.",
            "Use Run Code after small changes so errors are easier to fix.",
            "Review backend notes, output, and hints in the panel below the editor.",
        ],
        "note_chips": [
            "main.py is the active file",
            "Indentation matters",
            "Run often, fix one issue at a time",
        ],
        "hint_default": "Run the code and read the backend feedback carefully.",
        "tool_tab_label": "Run Code",
        "default_notification_title": "Python compiler feedback will appear here.",
        "default_notification_message": (
            "Use Run Code to execute the current Python program. The backend runner service "
            "will update this panel with the result."
        ),
        "default_notification_label": "Compiler feedback",
        "results_heading": "Run Results",
        "editor_tip_primary": "Tip: keep your indentation consistent across the whole file.",
        "editor_tip_secondary": "Backend notifications and execution output stay inside this panel.",
        "submit_idle_label": "Run Code",
        "submit_busy_label": "Running...",
        "action_meta": "Backend-driven compiler feedback in this panel",
        "default_error_title": "Compiler Details",
        "environment_error_title": "Compiler Environment Details",
        "runtime_error_kind": "python_runtime_error",
        "detail_caption": "Compiler service output",
        "environment_detail_caption": "Compiler environment output",
    },
    "php": {
        "headline": "Dedicated PHP Compiler",
        "workspace_default_title": "PHP Compiler Lab",
        "workspace_body": (
            "Work through the task in one place, then write, run, and test your PHP code safely inside the lesson workspace. "
            "You will see friendly guidance, backend feedback, and your program output below the editor."
        ),
        "file_name": "main.php",
        "tool_label": "PHP CLI runtime",
        "feedback_label": "Backend popup",
        "lesson_badge": "PHP lesson",
        "quick_start_steps": [
            "Read the task and keep your solution inside main.php.",
            "Use Run Code after small changes so errors are easier to fix.",
            "Review backend notes, output, and hints in the panel below the editor.",
        ],
        "note_chips": [
            "main.php is the active file",
            "Semicolons and dollar signs matter",
            "Run often, fix one issue at a time",
        ],
        "hint_default": "Run the code and read the backend feedback carefully.",
        "tool_tab_label": "Run Code",
        "default_notification_title": "PHP compiler feedback will appear here.",
        "default_notification_message": (
            "Use Run Code to execute the current PHP program. The backend runner service "
            "will update this panel with the result."
        ),
        "default_notification_label": "Compiler feedback",
        "results_heading": "Run Results",
        "editor_tip_primary": "Tip: keep the opening <?php tag at the top of the file.",
        "editor_tip_secondary": "Backend notifications and execution output stay inside this panel.",
        "submit_idle_label": "Run Code",
        "submit_busy_label": "Running...",
        "action_meta": "Backend-driven compiler feedback in this panel",
        "default_error_title": "Compiler Details",
        "environment_error_title": "Compiler Environment Details",
        "runtime_error_kind": "php_runtime_error",
        "detail_caption": "Compiler service output",
        "environment_detail_caption": "Compiler environment output",
    },
}


def build_runner_ui(lesson):
    rules = get_effective_activity_rules(lesson)
    language = get_effective_activity_language(lesson)
    config = CODE_RUNNER_UI.get(language, {})
    language_label = LANGUAGE_LABELS.get(language, "Code")
    file_name = config.get("file_name") or _default_runner_file_name(language)

    return {
        "uses_code_runner": uses_effective_code_runner(lesson),
        "use_dedicated_workspace": uses_effective_code_runner(lesson) and language in DEDICATED_CODE_RUNNER_LANGUAGES,
        "language": language,
        "language_label": language_label,
        "headline": config.get("headline") or f"{language_label} Code Runner",
        "workspace_title": lesson.activity_title or config.get("workspace_default_title") or "Code Runner Lab",
        "workspace_body": config.get("workspace_body")
        or "Write your solution, run it safely, and review the backend feedback below the editor.",
        "file_name": file_name,
        "tool_label": config.get("tool_label") or language_label,
        "feedback_label": config.get("feedback_label") or "Backend feedback",
        "lesson_badge": config.get("lesson_badge") or f"{language_label} lesson",
        "quick_start_steps": config.get("quick_start_steps")
        or [
            f"Read the task and keep your solution inside {file_name}.",
            "Run after small changes so errors are easier to fix.",
            "Use the results panel to check backend feedback, output, and hints.",
        ],
        "note_chips": config.get("note_chips")
        or [
            f"{file_name} is the active file",
            "Use the lesson example as a guide",
            "Run often, fix one issue at a time",
        ],
        "hint_default": config.get("hint_default") or "Run the code and read the backend feedback carefully.",
        "tool_tab_label": config.get("tool_tab_label") or "Run Code",
        "default_notification_title": config.get("default_notification_title")
        or f"{language_label} runner feedback will appear here.",
        "default_notification_message": config.get("default_notification_message")
        or "Use Run Code to receive backend feedback for this activity.",
        "default_notification_label": config.get("default_notification_label") or "Runner feedback",
        "results_heading": config.get("results_heading") or "Run Results",
        "editor_tip_primary": config.get("editor_tip_primary")
        or "Tip: compare your program with the lesson example before each run.",
        "editor_tip_secondary": config.get("editor_tip_secondary")
        or "Backend notifications and execution output stay inside this panel.",
        "submit_idle_label": config.get("submit_idle_label") or "Run Code",
        "submit_busy_label": config.get("submit_busy_label") or "Running...",
        "action_meta": config.get("action_meta") or "Backend-driven runner feedback in this panel",
        "default_error_title": config.get("default_error_title") or "Runner Details",
        "environment_error_title": config.get("environment_error_title") or "Runtime Environment Details",
        "runtime_error_kind": config.get("runtime_error_kind") or f"{language}_runtime_error",
        "detail_caption": config.get("detail_caption") or "Runner service output",
        "environment_detail_caption": config.get("environment_detail_caption") or "Runtime environment output",
        "starter_code_id": f"runner-starter-code-{lesson.id or lesson.order or 'lesson'}",
        "activity_rules": rules,
    }


def _default_runner_file_name(language):
    return {
        "csharp": "Program.cs",
        "python": "main.py",
        "php": "main.php",
    }.get(language, "main.txt")


def build_activity_form(lesson, progress):
    rules = get_effective_activity_rules(lesson)
    initial_response = progress.activity_response or rules.get("starter_code", "")
    form = ActivitySubmissionForm(initial={"response": initial_response})
    field = form.fields["response"]

    if uses_effective_code_runner(lesson):
        language = get_effective_activity_language(lesson)
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

    rules = get_effective_activity_rules(lesson)
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
        result.language or get_effective_activity_language(lesson),
        result.used_code_runner,
        result.execution_status,
        result.validation_result,
        result.runtime_available,
        result.timed_out,
        progress.activity_attempts,
    )

    return progress, result
