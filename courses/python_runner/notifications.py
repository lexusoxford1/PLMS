def build_python_system_notification(*, result):
    if result.is_correct:
        return {
            "channel": "panel",
            "source": "python_runner",
            "kind": "python_success",
            "label": "Run successful",
            "level": "success",
            "title": "Python code executed successfully",
            "message": result.explanation,
            "detail": result.program_output,
            "stage": "execute",
            "learning_suggestion": result.learning_suggestion,
        }

    if not result.runtime_available:
        return {
            "channel": "panel",
            "source": "python_runner",
            "kind": "python_runtime_unavailable",
            "label": "Setup issue",
            "level": "error",
            "title": "Python runtime unavailable",
            "message": result.explanation,
            "detail": result.errors,
            "stage": "runtime",
            "learning_suggestion": result.learning_suggestion,
        }

    if result.timed_out:
        return {
            "channel": "panel",
            "source": "python_runner",
            "kind": "python_timeout",
            "label": "Timed out",
            "level": "error",
            "title": "Python code timed out",
            "message": result.explanation,
            "detail": result.errors,
            "stage": "runtime",
            "learning_suggestion": result.learning_suggestion,
        }

    if result.execution_status == "error":
        return {
            "channel": "panel",
            "source": "python_runner",
            "kind": "python_runtime_error",
            "label": "Runtime error",
            "level": "error",
            "title": "Python code could not finish",
            "message": result.explanation,
            "detail": result.errors,
            "stage": "runtime",
            "learning_suggestion": result.learning_suggestion,
        }

    return {
        "channel": "panel",
        "source": "python_runner",
        "kind": "python_validation_feedback",
        "label": "Needs changes",
        "level": "warning",
        "title": "Python code needs changes",
        "message": result.explanation,
        "detail": result.program_output,
        "stage": "validation",
        "learning_suggestion": result.learning_suggestion,
    }
