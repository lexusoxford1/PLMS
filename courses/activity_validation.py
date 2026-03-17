import re

from courses.activity_results import ActivityEvaluationResult, ERROR_MESSAGE, SUCCESS_MESSAGE
from courses.activity_config import get_effective_activity_rules, uses_effective_code_runner
from courses.code_runner.validation import validate_code_activity_submission


def _compile_flags(rule):
    return 0 if rule.get("case_sensitive") else re.IGNORECASE


def _describe_missing(rule):
    count = rule.get("count", 1)
    description = rule.get("description") or rule.get("pattern", "the expected concept")
    if count <= 1:
        return description
    return f"{description} ({count} times)"


def validate_activity_submission(lesson, response):
    rules = get_effective_activity_rules(lesson)
    if uses_effective_code_runner(lesson) or rules.get("validator") == "code_runner":
        return validate_code_activity_submission(lesson, response)

    submission = (response or "").strip()
    if not submission:
        return ActivityEvaluationResult(
            is_correct=False,
            title=ERROR_MESSAGE,
            explanation="Your submission is empty. Add your answer or code before checking the activity.",
        )

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

    if missing_requirements or blocked_patterns:
        hint = rules.get("failure_hint") or lesson.activity_hint or (
            "Focus on the key steps shown in the lesson example and try again."
        )
        details = [hint]
        if missing_requirements:
            details.append("Check for: " + ", ".join(missing_requirements) + ".")
        if blocked_patterns:
            details.append("Avoid: " + ", ".join(blocked_patterns) + ".")
        return ActivityEvaluationResult(
            is_correct=False,
            title=ERROR_MESSAGE,
            explanation=" ".join(details),
        )

    explanation = rules.get("success_explanation") or (
        "Your submission includes the expected logic for this lesson activity."
    )
    return ActivityEvaluationResult(
        is_correct=True,
        title=SUCCESS_MESSAGE,
        explanation=explanation,
    )
