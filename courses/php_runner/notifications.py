def build_php_system_notification(*, result):
    if result.is_correct:
        return {
            "channel": "panel",
            "source": "php_runner",
            "kind": "php_success",
            "label": "Run successful",
            "level": "success",
            "title": "PHP code executed successfully",
            "message": result.explanation,
            "detail": result.program_output,
            "stage": "execute",
            "learning_suggestion": result.learning_suggestion,
        }

    if not result.runtime_available:
        return {
            "channel": "panel",
            "source": "php_runner",
            "kind": "php_runtime_unavailable",
            "label": "Setup issue",
            "level": "error",
            "title": "PHP runtime unavailable",
            "message": result.explanation,
            "detail": result.errors,
            "stage": "runtime",
            "learning_suggestion": result.learning_suggestion,
        }

    if result.timed_out:
        return {
            "channel": "panel",
            "source": "php_runner",
            "kind": "php_timeout",
            "label": "Timed out",
            "level": "error",
            "title": "PHP code timed out",
            "message": result.explanation,
            "detail": result.errors,
            "stage": "runtime",
            "learning_suggestion": result.learning_suggestion,
        }

    if result.execution_status == "error":
        return {
            "channel": "panel",
            "source": "php_runner",
            "kind": "php_runtime_error",
            "label": "Runtime error",
            "level": "error",
            "title": "PHP code could not finish",
            "message": result.explanation,
            "detail": result.errors,
            "stage": "runtime",
            "learning_suggestion": result.learning_suggestion,
        }

    return {
        "channel": "panel",
        "source": "php_runner",
        "kind": "php_validation_feedback",
        "label": "Needs changes",
        "level": "warning",
        "title": "PHP code needs changes",
        "message": result.explanation,
        "detail": result.program_output,
        "stage": "validation",
        "learning_suggestion": result.learning_suggestion,
    }
