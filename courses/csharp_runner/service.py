import re
import tempfile
from pathlib import Path

from django.conf import settings

from courses.activity_results import ActivityEvaluationResult, ERROR_MESSAGE, SUCCESS_MESSAGE
from courses.code_runner.feedback import build_beginner_friendly_error
from courses.code_runner.policies import find_blocked_construct

from .compiler import compile_and_execute_csharp
from .notifications import build_csharp_system_notification, extract_csharp_error_location, format_csharp_location


def validate_csharp_activity_submission(lesson, response):
    submission = (response or "").strip()
    if not submission:
        result = ActivityEvaluationResult(
            is_correct=False,
            title=ERROR_MESSAGE,
            explanation="Your submission is empty. Write your C# code before checking the activity.",
            execution_status="error",
            used_code_runner=True,
            language="csharp",
            details={"stage": "compile"},
        )
        result.notification = build_csharp_system_notification(result=result)
        return result

    max_source_bytes = int(getattr(settings, "CODE_RUNNER", {}).get("MAX_SOURCE_BYTES", 20000))
    if len(submission.encode("utf-8")) > max_source_bytes:
        result = ActivityEvaluationResult(
            is_correct=False,
            title=ERROR_MESSAGE,
            explanation="Your C# code is too large for this lesson compiler to check safely.",
            execution_status="error",
            used_code_runner=True,
            language="csharp",
            hint="Remove unrelated content and keep only the code required for this lesson.",
            details={"stage": "compile"},
        )
        result.notification = build_csharp_system_notification(result=result)
        return result

    blocked_construct = find_blocked_construct("csharp", submission)
    if blocked_construct:
        result = ActivityEvaluationResult(
            is_correct=False,
            title=ERROR_MESSAGE,
            explanation=blocked_construct.explanation,
            execution_status="error",
            used_code_runner=True,
            language="csharp",
            hint=blocked_construct.hint,
            learning_suggestion="Stay with the lesson's core C# features until the compiler accepts the solution.",
            details={"stage": "compile"},
        )
        result.notification = build_csharp_system_notification(result=result)
        return result

    rules = lesson.activity_validation_rules or {}
    source_issues = _evaluate_source_rules(submission, rules)
    timeout_seconds = int(
        rules.get("timeout_seconds") or getattr(settings, "CODE_RUNNER", {}).get("DEFAULT_TIMEOUT_SECONDS", 5)
    )
    with tempfile.TemporaryDirectory(dir=_create_workspace_root()) as temp_dir:
        execution_result = compile_and_execute_csharp(
            submission,
            workspace=Path(temp_dir),
            timeout_seconds=timeout_seconds,
        )
    error_location = extract_csharp_error_location(execution_result.errors)
    details = {**(execution_result.details or {}), "error_location": error_location}

    if execution_result.execution_status == "error":
        explanation, hint, suggestion = build_beginner_friendly_error(
            "csharp",
            execution_result.errors,
            timed_out=execution_result.timed_out,
            runtime_available=execution_result.runtime_available,
        )
        if error_location:
            location_text = format_csharp_location(error_location)
            explanation = f"{explanation} {location_text}".strip()
            hint = f"{hint} {location_text}".strip()

        result = ActivityEvaluationResult(
            is_correct=False,
            title=ERROR_MESSAGE,
            explanation=explanation,
            execution_status=execution_result.execution_status,
            program_output=execution_result.program_output,
            errors=execution_result.errors,
            hint=hint,
            learning_suggestion=suggestion,
            language="csharp",
            execution_time_ms=execution_result.execution_time_ms,
            runtime_available=execution_result.runtime_available,
            timed_out=execution_result.timed_out,
            used_code_runner=True,
            details=details,
        )
        result.notification = build_csharp_system_notification(result=result)
        return result

    output_match, output_message = _output_matches(rules, execution_result.program_output)
    if source_issues or not output_match:
        hints = [part for part in (source_issues, output_message, lesson.activity_hint) if part]
        result = ActivityEvaluationResult(
            is_correct=False,
            title=ERROR_MESSAGE,
            explanation=rules.get("incorrect_explanation") or "Your C# code compiled and ran, but it does not meet the lesson requirements yet.",
            execution_status=execution_result.execution_status,
            program_output=execution_result.program_output,
            errors=execution_result.errors,
            hint=" ".join(dict.fromkeys(hints)),
            learning_suggestion=rules.get("learning_suggestion") or _default_learning_suggestion(),
            language="csharp",
            execution_time_ms=execution_result.execution_time_ms,
            runtime_available=execution_result.runtime_available,
            timed_out=execution_result.timed_out,
            used_code_runner=True,
            details=details,
        )
        result.notification = build_csharp_system_notification(result=result)
        return result

    result = ActivityEvaluationResult(
        is_correct=True,
        title=SUCCESS_MESSAGE,
        explanation=rules.get("success_explanation") or "Your C# code compiled and executed successfully.",
        execution_status=execution_result.execution_status,
        program_output=execution_result.program_output,
        errors=execution_result.errors,
        hint=rules.get("success_hint", ""),
        learning_suggestion=rules.get("learning_suggestion") or "Try refactoring one part of the solution to make the code even clearer.",
        language="csharp",
        execution_time_ms=execution_result.execution_time_ms,
        runtime_available=execution_result.runtime_available,
        timed_out=execution_result.timed_out,
        used_code_runner=True,
        details=details,
    )
    result.notification = build_csharp_system_notification(result=result)
    return result


def _create_workspace_root():
    execution_root = Path(
        getattr(settings, "CODE_RUNNER", {}).get("EXECUTION_ROOT", settings.BASE_DIR / ".code_runner")
    )
    execution_root.mkdir(parents=True, exist_ok=True)
    return execution_root


def _evaluate_source_rules(submission, rules):
    required_patterns = rules.get("required_patterns", [])
    forbidden_patterns = rules.get("forbidden_patterns", [])

    missing_requirements = []
    for rule in required_patterns:
        pattern = rule.get("pattern")
        if not pattern:
            continue
        matches = re.findall(pattern, submission, flags=_compile_flags(rule))
        if len(matches) < int(rule.get("count", 1)):
            missing_requirements.append(_describe_missing(rule))

    blocked_patterns = []
    for rule in forbidden_patterns:
        pattern = rule.get("pattern")
        if pattern and re.search(pattern, submission, flags=_compile_flags(rule)):
            blocked_patterns.append(rule.get("description") or pattern)

    details = []
    if missing_requirements:
        details.append("Add or fix: " + ", ".join(missing_requirements) + ".")
    if blocked_patterns:
        details.append("Remove: " + ", ".join(blocked_patterns) + ".")
    return " ".join(details)


def _output_matches(rules, program_output):
    if rules.get("expected_output_lines"):
        rules = {**rules, "expected_output": "\n".join(rules["expected_output_lines"])}

    normalized_output = _normalize_output(
        program_output,
        ignore_case=rules.get("ignore_case", False),
        ignore_whitespace=rules.get("ignore_whitespace", True),
    )
    comparison = rules.get("output_comparison", "exact")
    expected_output = rules.get("expected_output")
    expected_contains = rules.get("expected_output_contains", [])
    expected_patterns = rules.get("expected_output_patterns", [])
    if isinstance(expected_contains, str):
        expected_contains = [expected_contains]
    if isinstance(expected_patterns, str):
        expected_patterns = [expected_patterns]
    min_output_lines = int(rules.get("min_output_lines", 0) or 0)

    if min_output_lines and len([line for line in normalized_output.split("\n") if line]) < min_output_lines:
        return False, f"Your program should print at least {min_output_lines} line(s) of output."

    if expected_patterns:
        missing_patterns = [
            pattern for pattern in expected_patterns if not re.search(pattern, normalized_output, flags=_regex_flags(rules))
        ]
        if missing_patterns:
            return False, "The output is missing one or more expected C# results."

    if expected_contains:
        missing_fragments = [
            fragment
            for fragment in expected_contains
            if _normalize_output(
                fragment,
                ignore_case=rules.get("ignore_case", False),
                ignore_whitespace=rules.get("ignore_whitespace", True),
            )
            not in normalized_output
        ]
        if missing_fragments:
            return False, "Make sure the C# output includes the expected text shown in the lesson."

    if expected_output is None:
        return True, ""

    normalized_expected = _normalize_output(
        expected_output,
        ignore_case=rules.get("ignore_case", False),
        ignore_whitespace=rules.get("ignore_whitespace", True),
    )
    if comparison == "contains":
        if normalized_expected in normalized_output:
            return True, ""
    elif comparison == "regex":
        if re.search(expected_output, normalized_output, flags=_regex_flags(rules)):
            return True, ""
    elif normalized_output == normalized_expected:
        return True, ""

    preview = expected_output.strip() if isinstance(expected_output, str) else str(expected_output)
    return False, f"Expected output: {preview}"


def _default_learning_suggestion():
    return "Trace the C# program from Main() and check what should happen before and after each statement."


def _normalize_output(value, *, ignore_case=False, ignore_whitespace=True):
    text = (value or "").replace("\r\n", "\n").strip()
    if ignore_whitespace:
        text = "\n".join(line.strip() for line in text.split("\n"))
    if ignore_case:
        text = text.lower()
    return text


def _compile_flags(rule):
    return 0 if rule.get("case_sensitive") else re.IGNORECASE


def _regex_flags(rules):
    return 0 if rules.get("case_sensitive_output") else re.IGNORECASE


def _describe_missing(rule):
    count = rule.get("count", 1)
    description = rule.get("description") or rule.get("pattern", "the expected concept")
    if count <= 1:
        return description
    return f"{description} ({count} times)"
