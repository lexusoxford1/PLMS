COURSE_BADGE_STYLES = {
    ("python", "enrollment"): {
        "title": "Python Pathfinder",
        "glyph": "Py",
        "icon": "trail",
        "accent_label": "First unlock",
        "pattern": "orbit",
        "primary": "#2563eb",
        "secondary": "#60a5fa",
        "accent": "#22d3ee",
        "surface": "#f8fbff",
        "ink": "#14213d",
        "stage_label": "Enrollment Badge",
        "xp_reward": 40,
    },
    ("python", "completion"): {
        "title": "Python Supernova",
        "glyph": "Py+",
        "icon": "supernova",
        "accent_label": "Course mastered",
        "pattern": "burst",
        "primary": "#1d4ed8",
        "secondary": "#93c5fd",
        "accent": "#facc15",
        "surface": "#f7fbff",
        "ink": "#172554",
        "stage_label": "Completion Badge",
        "xp_reward": 120,
    },
    ("php", "enrollment"): {
        "title": "PHP Pulse",
        "glyph": "PHP",
        "icon": "pulse",
        "accent_label": "Path started",
        "pattern": "matrix",
        "primary": "#0f766e",
        "secondary": "#5eead4",
        "accent": "#38bdf8",
        "surface": "#f5fffd",
        "ink": "#0f172a",
        "stage_label": "Enrollment Badge",
        "xp_reward": 40,
    },
    ("php", "completion"): {
        "title": "PHP Prism",
        "glyph": "PHP+",
        "icon": "prism",
        "accent_label": "Final unlock",
        "pattern": "crystal",
        "primary": "#0f4c81",
        "secondary": "#7dd3fc",
        "accent": "#f59e0b",
        "surface": "#f8fdff",
        "ink": "#082f49",
        "stage_label": "Completion Badge",
        "xp_reward": 120,
    },
    ("csharp", "enrollment"): {
        "title": "C# Catalyst",
        "glyph": "C#",
        "icon": "launch",
        "accent_label": "Journey started",
        "pattern": "prism",
        "primary": "#db2777",
        "secondary": "#fb7185",
        "accent": "#fbbf24",
        "surface": "#fff8fb",
        "ink": "#4a044e",
        "stage_label": "Enrollment Badge",
        "xp_reward": 40,
    },
    ("csharp", "completion"): {
        "title": "C# Horizon",
        "glyph": "C#+",
        "icon": "shield",
        "accent_label": "Completion glow",
        "pattern": "hex",
        "primary": "#be123c",
        "secondary": "#fb7185",
        "accent": "#fcd34d",
        "surface": "#fff8fb",
        "ink": "#500724",
        "stage_label": "Completion Badge",
        "xp_reward": 120,
    },
    ("default", "enrollment"): {
        "title": "Course Kickoff",
        "glyph": "GO",
        "icon": "trail",
        "accent_label": "Enrollment reward",
        "pattern": "orbit",
        "primary": "#2563eb",
        "secondary": "#60a5fa",
        "accent": "#22d3ee",
        "surface": "#f8fbff",
        "ink": "#0f172a",
        "stage_label": "Enrollment Badge",
        "xp_reward": 40,
    },
    ("default", "completion"): {
        "title": "Course Finish",
        "glyph": "WIN",
        "icon": "shield",
        "accent_label": "Completion reward",
        "pattern": "burst",
        "primary": "#1d4ed8",
        "secondary": "#93c5fd",
        "accent": "#facc15",
        "surface": "#f8fbff",
        "ink": "#172554",
        "stage_label": "Completion Badge",
        "xp_reward": 120,
    },
}

PLATFORM_BADGES = [
    {
        "criteria_key": "milestone:first-steps",
        "award_type": "milestone",
        "name": "First Steps",
        "description": "Enroll in your first course and open your achievement journey.",
        "metric": "enrolled_courses",
        "target": 1,
        "glyph": "L1",
        "icon": "compass",
        "accent_label": "Starter XP",
        "pattern": "orbit",
        "primary": "#2563eb",
        "secondary": "#93c5fd",
        "accent": "#22d3ee",
        "surface": "#f8fbff",
        "ink": "#14213d",
        "stage_label": "Milestone Badge",
        "xp_reward": 60,
    },
    {
        "criteria_key": "milestone:course-collector",
        "award_type": "milestone",
        "name": "Course Collector",
        "description": "Enroll in all available programming tracks and build a full learning lineup.",
        "metric": "enrolled_courses",
        "target": 3,
        "glyph": "3X",
        "icon": "stack",
        "accent_label": "Lineup ready",
        "pattern": "matrix",
        "primary": "#0f766e",
        "secondary": "#5eead4",
        "accent": "#38bdf8",
        "surface": "#f5fffd",
        "ink": "#0f172a",
        "stage_label": "Milestone Badge",
        "xp_reward": 120,
    },
    {
        "criteria_key": "milestone:lesson-spark",
        "award_type": "milestone",
        "name": "Lesson Spark",
        "description": "Complete 6 lessons to show consistent momentum across the platform.",
        "metric": "completed_lessons",
        "target": 6,
        "glyph": "6",
        "icon": "spark",
        "accent_label": "Momentum up",
        "pattern": "burst",
        "primary": "#f97316",
        "secondary": "#fdba74",
        "accent": "#38bdf8",
        "surface": "#fffaf5",
        "ink": "#7c2d12",
        "stage_label": "Milestone Badge",
        "xp_reward": 90,
    },
    {
        "criteria_key": "milestone:quiz-striker",
        "award_type": "milestone",
        "name": "Quiz Striker",
        "description": "Pass 3 quizzes and prove your learning is sticking.",
        "metric": "passed_quizzes",
        "target": 3,
        "glyph": "Q3",
        "icon": "bolt",
        "accent_label": "Quiz streak",
        "pattern": "hex",
        "primary": "#0f4c81",
        "secondary": "#7dd3fc",
        "accent": "#22d3ee",
        "surface": "#f7fcff",
        "ink": "#082f49",
        "stage_label": "Milestone Badge",
        "xp_reward": 100,
    },
    {
        "criteria_key": "milestone:perfect-pulse",
        "award_type": "milestone",
        "name": "Perfect Pulse",
        "description": "Hit a 100% score on any quiz to unlock this precision badge.",
        "metric": "perfect_quizzes",
        "target": 1,
        "glyph": "100",
        "icon": "target",
        "accent_label": "Perfect hit",
        "pattern": "crystal",
        "primary": "#dc2626",
        "secondary": "#fca5a5",
        "accent": "#facc15",
        "surface": "#fff8f8",
        "ink": "#7f1d1d",
        "stage_label": "Milestone Badge",
        "xp_reward": 110,
    },
    {
        "criteria_key": "milestone:graduation-glow",
        "award_type": "milestone",
        "name": "Graduation Glow",
        "description": "Complete your first course and step into the next level as a finisher.",
        "metric": "completed_courses",
        "target": 1,
        "glyph": "G1",
        "icon": "trophy",
        "accent_label": "First finish",
        "pattern": "prism",
        "primary": "#7c3aed",
        "secondary": "#c4b5fd",
        "accent": "#facc15",
        "surface": "#faf8ff",
        "ink": "#3b0764",
        "stage_label": "Milestone Badge",
        "xp_reward": 150,
    },
    {
        "criteria_key": "milestone:triple-crown",
        "award_type": "milestone",
        "name": "Triple Crown",
        "description": "Complete all three programming courses and become a full-path finisher.",
        "metric": "completed_courses",
        "target": 3,
        "glyph": "3C",
        "icon": "crown",
        "accent_label": "Top tier",
        "pattern": "hex",
        "primary": "#0f172a",
        "secondary": "#94a3b8",
        "accent": "#facc15",
        "surface": "#fbfcff",
        "ink": "#111827",
        "stage_label": "Milestone Badge",
        "xp_reward": 260,
    },
]

PLATFORM_BADGE_MAP = {definition["criteria_key"]: definition for definition in PLATFORM_BADGES}


def resolve_course_family(course):
    slug = str(getattr(course, "slug", "") or "").lower()
    title = str(getattr(course, "title", "") or "").lower()
    lookup = f"{slug} {title}"
    if "python" in lookup:
        return "python"
    if "php" in lookup:
        return "php"
    if "csharp" in lookup or "c#" in lookup:
        return "csharp"
    return "default"


def build_course_criteria_key(course, award_type):
    return f"course:{course.slug}:{award_type}"


def get_course_badge_definition(course, award_type):
    family = resolve_course_family(course)
    spec = COURSE_BADGE_STYLES.get((family, award_type), COURSE_BADGE_STYLES[("default", award_type)])
    if award_type == "enrollment":
        description = f"Awarded when you enroll in {course.title} and begin your guided path."
    else:
        description = f"Awarded after you finish every lesson and pass the final quiz in {course.title}."

    return {
        **spec,
        "criteria_key": build_course_criteria_key(course, award_type),
        "name": f"{course.title} - {spec['title']}",
        "description": description,
        "family": family,
        "theme": f"{family}-{award_type}",
    }


def get_platform_badge_definitions():
    return PLATFORM_BADGES


def get_platform_badge_definition(criteria_key):
    definition = PLATFORM_BADGE_MAP[criteria_key]
    return {
        **definition,
        "family": "milestone",
        "theme": f"milestone-{criteria_key.split(':', 1)[1]}",
    }


def get_badge_definition(badge):
    if badge.course_id:
        return get_course_badge_definition(badge.course, badge.award_type)
    if badge.criteria_key and badge.criteria_key in PLATFORM_BADGE_MAP:
        return get_platform_badge_definition(badge.criteria_key)
    fallback = PLATFORM_BADGE_MAP["milestone:first-steps"]
    return {
        **fallback,
        "name": badge.name,
        "description": badge.description,
        "criteria_key": badge.criteria_key,
        "theme": "milestone-fallback",
        "family": "milestone",
    }


def get_badge_visual_spec(badge):
    return get_badge_definition(badge)


def get_badge_defaults(*, course=None, award_type=None, criteria_key=None):
    if course is not None:
        definition = get_course_badge_definition(course, award_type)
    else:
        definition = get_platform_badge_definition(criteria_key)

    return {
        "criteria_key": definition["criteria_key"],
        "name": definition["name"],
        "description": definition["description"],
        "xp_reward": definition["xp_reward"],
        "is_active": True,
    }
