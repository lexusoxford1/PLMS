from .feedback import language_label


def build_code_runner_system_notification(*, result):
    language = result.language or "code"
    label = language_label(language)
    source = f"{language}_runner"

    if result.is_correct:
        return {
            "channel": "panel",
            "source": source,
            "kind": f"{language}_success",
            "label": "Run successful",
            "level": "success",
            "title": f"{label} code executed successfully",
            "message": result.explanation,
            "detail": result.program_output,
            "stage": "execute",
            "learning_suggestion": result.learning_suggestion,
        }

    if not result.runtime_available:
        return {
            "channel": "panel",
            "source": source,
            "kind": f"{language}_runtime_unavailable",
            "label": "Setup issue",
            "level": "error",
            "title": f"{label} runtime unavailable",
            "message": result.explanation,
            "detail": result.errors,
            "stage": "runtime",
            "learning_suggestion": result.learning_suggestion,
        }

    if result.timed_out:
        return {
            "channel": "panel",
            "source": source,
            "kind": f"{language}_timeout",
            "label": "Timed out",
            "level": "error",
            "title": f"{label} code timed out",
            "message": result.explanation,
            "detail": result.errors,
            "stage": "runtime",
            "learning_suggestion": result.learning_suggestion,
        }

    if result.execution_status == "error":
        return {
            "channel": "panel",
            "source": source,
            "kind": f"{language}_runtime_error",
            "label": "Runtime error",
            "level": "error",
            "title": f"{label} code could not finish",
            "message": result.explanation,
            "detail": result.errors,
            "stage": "runtime",
            "learning_suggestion": result.learning_suggestion,
        }

    return {
        "channel": "panel",
        "source": source,
        "kind": f"{language}_validation_feedback",
        "label": "Needs changes",
        "level": "warning",
        "title": f"{label} code needs changes",
        "message": result.explanation,
        "detail": result.program_output,
        "stage": "validation",
        "learning_suggestion": result.learning_suggestion,
    }
