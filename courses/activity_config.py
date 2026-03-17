from copy import deepcopy

from .course_seed import COURSE_DEFINITIONS


SEEDED_COURSES = {course_definition["slug"]: course_definition for course_definition in COURSE_DEFINITIONS}


def get_effective_activity_rules(lesson):
    raw_rules = deepcopy(lesson.activity_validation_rules or {})
    seeded_rules = _get_seeded_activity_rules(lesson)
    if not seeded_rules:
        return raw_rules

    raw_language = (raw_rules.get("language") or "").lower()
    seeded_language = (seeded_rules.get("language") or "").lower()

    if raw_rules.get("validator") == "code_runner" or (raw_language and raw_language == seeded_language):
        merged = deepcopy(seeded_rules)
        merged.update(raw_rules)
        return merged

    return deepcopy(seeded_rules)


def get_effective_activity_language(lesson):
    return (get_effective_activity_rules(lesson).get("language") or "").lower()


def uses_effective_code_runner(lesson):
    rules = get_effective_activity_rules(lesson)
    return bool(rules.get("validator") == "code_runner" or rules.get("language"))


def _get_seeded_activity_rules(lesson):
    course_definition = SEEDED_COURSES.get(getattr(getattr(lesson, "course", None), "slug", ""))
    if not course_definition:
        return None

    lessons = course_definition.get("lessons", [])
    order = int(getattr(lesson, "order", 0) or 0)
    if order < 1 or order > len(lessons):
        return None

    return lessons[order - 1].get("activity_validation") or None
