import re

from django.conf import settings

from courses.activity_results import ActivityEvaluationResult, ERROR_MESSAGE, SUCCESS_MESSAGE
from courses.activity_config import get_effective_activity_rules
from courses.code_runner.executors import execute_code
from courses.code_runner.feedback import build_beginner_friendly_error
from courses.code_runner.policies import find_blocked_construct

from .notifications import build_php_system_notification


def validate_php_activity_submission(lesson, response):
    submission = (response or "").strip()
    rules = get_effective_activity_rules(lesson)

    if not submission:
        result = ActivityEvaluationResult(
            is_correct=False,
            title=ERROR_MESSAGE,
            explanation="Your submission is empty. Write your PHP code before checking the activity.",
            execution_status="error",
            used_code_runner=True,
            language="php",
            details={"stage": "execute"},
        )
        result.notification = build_php_system_notification(result=result)
        return result

    max_source_bytes = int(getattr(settings, "CODE_RUNNER", {}).get("MAX_SOURCE_BYTES", 20000))
    if len(submission.encode("utf-8")) > max_source_bytes:
        result = ActivityEvaluationResult(
            is_correct=False,
            title=ERROR_MESSAGE,
            explanation="Your PHP code is too large for this lesson runner to check safely.",
            execution_status="error",
            used_code_runner=True,
            language="php",
            hint="Remove unrelated content and keep only the code required for this lesson.",
            details={"stage": "execute"},
        )
        result.notification = build_php_system_notification(result=result)
        return result

    blocked_construct = find_blocked_construct("php", submission)
    if blocked_construct:
        result = ActivityEvaluationResult(
            is_correct=False,
            title=ERROR_MESSAGE,
            explanation=blocked_construct.explanation,
            execution_status="error",
            used_code_runner=True,
            language="php",
            hint=blocked_construct.hint,
            learning_suggestion="Stay with the lesson's core PHP features until the runner accepts the solution.",
            details={"stage": "execute"},
        )
        result.notification = build_php_system_notification(result=result)
        return result

    source_issues = _evaluate_source_rules(submission, rules)
    execution_result = execute_code(
        "php",
        submission,
        timeout_seconds=int(
            rules.get("timeout_seconds") or getattr(settings, "CODE_RUNNER", {}).get("DEFAULT_TIMEOUT_SECONDS", 5)
        ),
    )

    if execution_result.execution_status == "error":
        explanation, hint, suggestion = build_beginner_friendly_error(
            "php",
            execution_result.errors,
            timed_out=execution_result.timed_out,
            runtime_available=execution_result.runtime_available,
        )
        result = ActivityEvaluationResult(
            is_correct=False,
            title=ERROR_MESSAGE,
            explanation=explanation,
            execution_status=execution_result.execution_status,
            program_output=execution_result.program_output,
            errors=execution_result.errors,
            hint=hint,
            learning_suggestion=suggestion,
            language="php",
            execution_time_ms=execution_result.execution_time_ms,
            runtime_available=execution_result.runtime_available,
            timed_out=execution_result.timed_out,
            used_code_runner=True,
            details=execution_result.details,
        )
        result.notification = build_php_system_notification(result=result)
        return result

    output_match, output_message = _output_matches(rules, execution_result.program_output)
    accept_alternative_solutions = bool(rules.get("accept_alternative_solutions"))

    if not output_match or (source_issues and not accept_alternative_solutions):
        hints = []
        if source_issues and not accept_alternative_solutions:
            hints.append(source_issues)
        if output_message:
            hints.append(output_message)
        if lesson.activity_hint:
            hints.append(lesson.activity_hint)
        result = ActivityEvaluationResult(
            is_correct=False,
            title=ERROR_MESSAGE,
            explanation=rules.get("incorrect_explanation")
            or "Your PHP code ran, but it does not meet the lesson requirements yet.",
            execution_status=execution_result.execution_status,
            program_output=execution_result.program_output,
            errors=execution_result.errors,
            hint=" ".join(dict.fromkeys(hints)),
            learning_suggestion=rules.get("learning_suggestion") or _default_learning_suggestion(),
            language="php",
            execution_time_ms=execution_result.execution_time_ms,
            runtime_available=execution_result.runtime_available,
            timed_out=execution_result.timed_out,
            used_code_runner=True,
            details=execution_result.details,
        )
        result.notification = build_php_system_notification(result=result)
        return result

    result = ActivityEvaluationResult(
        is_correct=True,
        title=SUCCESS_MESSAGE,
        explanation=rules.get("success_explanation") or "Your PHP code executed successfully.",
        execution_status=execution_result.execution_status,
        program_output=execution_result.program_output,
        errors=execution_result.errors,
        hint=rules.get("success_hint", ""),
        learning_suggestion=rules.get("learning_suggestion")
        or "Try refactoring one part of the solution to make the code even clearer.",
        language="php",
        execution_time_ms=execution_result.execution_time_ms,
        runtime_available=execution_result.runtime_available,
        timed_out=execution_result.timed_out,
        used_code_runner=True,
        details=execution_result.details,
    )
    result.notification = build_php_system_notification(result=result)
    return result


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
            return False, "The output is missing one or more expected PHP results."

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
            return False, "Make sure the PHP output includes the expected text shown in the lesson."

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
    return "Trace the PHP script from top to bottom and check what should happen before and after each line."


def _normalize_output(value, *, ignore_case=False, ignore_whitespace=True):
    text = re.sub(r"<br\s*/?>", "\n", value or "", flags=re.IGNORECASE)
    text = text.replace("\r\n", "\n").strip()
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
