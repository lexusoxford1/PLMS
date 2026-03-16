from textwrap import dedent

from django.utils.html import escape


def build_lesson_content(paragraphs, code, concepts):
    paragraph_html = "".join(f"<p>{escape(paragraph)}</p>" for paragraph in paragraphs)
    concept_items = "".join(f"<li>{escape(concept)}</li>" for concept in concepts)
    return (
        f"{paragraph_html}"
        "<h3>Example Code</h3>"
        f"<pre><code>{escape(dedent(code).strip())}</code></pre>"
        "<h3>Key Concepts</h3>"
        f"<ul>{concept_items}</ul>"
    )


def build_activity_content(description, tasks, starter_code=""):
    task_items = "".join(f"<li>{escape(task)}</li>" for task in tasks)
    parts = [
        f"<p>{escape(description)}</p>",
        "<h3>What You Need To Do</h3>",
        f"<ol>{task_items}</ol>",
    ]
    if starter_code:
        parts.extend(
            [
                "<h3>Starter Code</h3>",
                f"<pre><code>{escape(dedent(starter_code).strip())}</code></pre>",
            ]
        )
    return "".join(parts)


def required_pattern(pattern, description, count=1, *, case_sensitive=False):
    return {
        "pattern": dedent(pattern).strip(),
        "description": description,
        "count": count,
        "case_sensitive": case_sensitive,
    }


def build_activity_validation(required_patterns, success_explanation, failure_hint, forbidden_patterns=None):
    return {
        "required_patterns": required_patterns,
        "forbidden_patterns": forbidden_patterns or [],
        "success_explanation": success_explanation,
        "failure_hint": failure_hint,
    }


def build_code_activity_validation(
    language,
    expected_output,
    success_explanation,
    failure_hint,
    *,
    starter_code="",
    output_comparison="exact",
    expected_output_contains=None,
    expected_output_patterns=None,
    required_patterns=None,
    forbidden_patterns=None,
    learning_suggestion="",
    timeout_seconds=5,
    ignore_case=False,
    ignore_whitespace=True,
    min_output_lines=0,
    concept_review=None,
):
    return {
        "validator": "code_runner",
        "language": language,
        "starter_code": dedent(starter_code).strip(),
        "expected_output": dedent(expected_output).strip() if isinstance(expected_output, str) else expected_output,
        "expected_output_contains": expected_output_contains or [],
        "expected_output_patterns": expected_output_patterns or [],
        "output_comparison": output_comparison,
        "required_patterns": required_patterns or [],
        "forbidden_patterns": forbidden_patterns or [],
        "success_explanation": success_explanation,
        "failure_hint": failure_hint,
        "learning_suggestion": learning_suggestion,
        "timeout_seconds": timeout_seconds,
        "ignore_case": ignore_case,
        "ignore_whitespace": ignore_whitespace,
        "min_output_lines": min_output_lines,
        "concept_review": concept_review or {},
    }
