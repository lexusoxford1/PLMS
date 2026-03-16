import re


CSHARP_ERROR_LOCATION_PATTERN = re.compile(
    r"(?P<file>[\w./\\-]+)\((?P<line>\d+),(?P<column>\d+)\):\s*(?P<severity>error|warning)\s*(?P<code>CS\d+):\s*(?P<message>.+)"
)


def extract_csharp_error_location(errors):
    match = CSHARP_ERROR_LOCATION_PATTERN.search(errors or "")
    if not match:
        return {}
    return {
        "file": match.group("file"),
        "line": int(match.group("line")),
        "column": int(match.group("column")),
        "code": match.group("code"),
        "message": match.group("message").strip(),
    }


def build_csharp_system_notification(*, result):
    stage = (result.details or {}).get("stage", "execute")
    location = (result.details or {}).get("error_location") or {}
    environment_issue = (result.details or {}).get("environment_issue")

    if result.is_correct:
        return {
            "channel": "popup",
            "source": "csharp_compiler",
            "kind": "csharp_success",
            "label": "Run successful",
            "level": "success",
            "title": "C# code executed successfully",
            "message": result.explanation,
            "detail": result.program_output,
            "stage": stage,
            "location": location,
            "learning_suggestion": result.learning_suggestion,
        }

    if result.execution_status == "error" and stage == "compile":
        if environment_issue:
            return {
                "channel": "popup",
                "source": "csharp_compiler",
                "kind": "csharp_compiler_environment_error",
                "label": "Setup issue",
                "level": "error",
                "title": "C# compiler setup issue",
                "message": result.explanation,
                "detail": result.errors,
                "stage": "compile",
                "location": location,
                "learning_suggestion": result.learning_suggestion,
            }

        location_text = format_csharp_location(location)
        message = "The C# compiler could not build your code."
        if location_text:
            message = f"{message} {location_text}"
        return {
            "channel": "popup",
            "source": "csharp_compiler",
            "kind": "csharp_compile_error",
            "label": "Compilation error",
            "level": "error",
            "title": "C# compilation error",
            "message": message,
            "detail": result.errors,
            "stage": "compile",
            "location": location,
            "learning_suggestion": result.learning_suggestion,
        }

    if result.execution_status == "error":
        return {
            "channel": "popup",
            "source": "csharp_compiler",
            "kind": "csharp_runtime_error",
            "label": "Runtime error",
            "level": "error",
            "title": "C# runtime error",
            "message": "Your C# code compiled, but it failed while running.",
            "detail": result.errors,
            "stage": "runtime",
            "location": location,
            "learning_suggestion": result.learning_suggestion,
        }

    return {
        "channel": "popup",
        "source": "csharp_compiler",
        "kind": "csharp_validation_feedback",
        "label": "Needs changes",
        "level": "error",
        "title": "C# code needs changes",
        "message": result.explanation,
        "detail": result.program_output,
        "stage": "validation",
        "location": location,
        "learning_suggestion": result.learning_suggestion,
    }


def format_csharp_location(location):
    if not location:
        return ""
    return (
        f"The compiler pointed to {location.get('file', 'Program.cs')} "
        f"line {location.get('line')}, column {location.get('column')}."
    )
