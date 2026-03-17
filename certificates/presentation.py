from hashlib import md5
from types import SimpleNamespace

from django.conf import settings
from django.utils import timezone


CERTIFICATE_THEMES = [
    {
        "name": "azure",
        "primary": "#0f7bdc",
        "secondary": "#114b95",
        "accent": "#ff7b1c",
        "surface": "#fffdf7",
        "surface_tint": "#eef5ff",
        "soft": "#dce8ff",
        "ink": "#102542",
        "muted": "#4f647a",
        "seal": "#f0f5ff",
    },
    {
        "name": "navy",
        "primary": "#1553b7",
        "secondary": "#0f2e72",
        "accent": "#f59e0b",
        "surface": "#fffdf8",
        "surface_tint": "#eff4ff",
        "soft": "#dae6ff",
        "ink": "#14213d",
        "muted": "#566376",
        "seal": "#f2f6ff",
    },
    {
        "name": "teal",
        "primary": "#0e7490",
        "secondary": "#164e63",
        "accent": "#fb923c",
        "surface": "#fffdf7",
        "surface_tint": "#eefcfb",
        "soft": "#d5f3f1",
        "ink": "#12313a",
        "muted": "#4f666d",
        "seal": "#f2fffd",
    },
    {
        "name": "indigo",
        "primary": "#4f46e5",
        "secondary": "#312e81",
        "accent": "#f97316",
        "surface": "#fffdf8",
        "surface_tint": "#f3f1ff",
        "soft": "#e2dcff",
        "ink": "#1f2554",
        "muted": "#62688a",
        "seal": "#f7f5ff",
    },
]


def pick_certificate_theme(seed_text):
    seed = seed_text or "plms-certificate"
    index = int(md5(seed.encode("utf-8")).hexdigest()[:8], 16) % len(CERTIFICATE_THEMES)
    return CERTIFICATE_THEMES[index]


def build_theme_style(theme):
    return "; ".join(
        [
            f"--certificate-primary: {theme['primary']}",
            f"--certificate-secondary: {theme['secondary']}",
            f"--certificate-accent: {theme['accent']}",
            f"--certificate-surface: {theme['surface']}",
            f"--certificate-surface-tint: {theme['surface_tint']}",
            f"--certificate-soft: {theme['soft']}",
            f"--certificate-ink: {theme['ink']}",
            f"--certificate-muted: {theme['muted']}",
            f"--certificate-seal: {theme['seal']}",
        ]
    )


def build_course_monogram(title):
    words = [word[:1].upper() for word in (title or "").split() if word[:1].isalnum()]
    if len(words) >= 2:
        return "".join(words[:2])
    if words:
        return words[0][:2]
    return "PL"


def get_certificate_signatory_for_course(course):
    instructor = getattr(course, "created_by", None)
    if instructor:
        return {
            "name": instructor.get_full_name() or instructor.username,
            "title": "Course Instructor",
        }

    return {
        "name": getattr(settings, "CERTIFICATE_SIGNATORY_NAME", "PLMS Learning Office"),
        "title": getattr(settings, "CERTIFICATE_SIGNATORY_TITLE", "Program Director"),
    }


def get_certificate_signatory(certificate):
    return get_certificate_signatory_for_course(certificate.course)


def build_learner_certificate_profile(user):
    return {
        "learner_name": user.get_certificate_display_name(),
        "learner_identity_line": user.get_certificate_identity_line(),
        "learner_email": user.email.strip(),
    }


def build_default_certificate_preview(course=None):
    if course is None:
        course = SimpleNamespace(
            title="Your Course Title",
            slug="default-certificate-preview",
            created_by=None,
            get_difficulty_display=lambda: "Completion Reward",
        )
    return _build_certificate_presentation(
        course=course,
        learner_name="",
        learner_identity_line="",
        learner_email="",
        certificate_number="",
        issued_on=None,
        badge_name="",
        is_preview=True,
    )


def build_certificate_preview_model(course, user=None):
    learner_name = ""
    learner_identity_line = ""
    learner_email = ""
    if user and getattr(user, "is_authenticated", False):
        profile = build_learner_certificate_profile(user)
        learner_name = profile["learner_name"]
        learner_identity_line = profile["learner_identity_line"]
        learner_email = profile["learner_email"]
    return _build_certificate_presentation(
        course=course,
        learner_name=learner_name,
        learner_identity_line=learner_identity_line,
        learner_email=learner_email,
        certificate_number="",
        issued_on=None,
        badge_name="",
        is_preview=True,
    )


def _build_certificate_presentation(
    course,
    learner_name,
    learner_identity_line,
    learner_email,
    certificate_number,
    issued_on,
    badge_name,
    is_preview,
):
    theme = pick_certificate_theme(course.slug or course.title or certificate_number)
    signatory = get_certificate_signatory_for_course(course)
    issued_short = issued_on.strftime("%b %d, %Y") if issued_on else "Locked"
    issued_date = issued_on.strftime("%B %d, %Y") if issued_on else ""
    profile_fact_label = "Verified Email" if learner_email else "Learner Profile"
    profile_fact_value = learner_email or learner_identity_line

    return {
        "brand_name": getattr(settings, "CERTIFICATE_BRAND_NAME", "PLMS Academy"),
        "brand_subtitle": getattr(
            settings,
            "CERTIFICATE_BRAND_SUBTITLE",
            "Programming Learning Management System",
        ),
        "completion_label": "Certificate of Completion",
        "course_title": course.title,
        "course_track": course.get_difficulty_display(),
        "course_monogram": build_course_monogram(course.title),
        "certificate_number": certificate_number,
        "issued_at": issued_on,
        "issued_date": issued_date,
        "issued_short": issued_short,
        "learner_name": learner_name,
        "learner_identity_line": learner_identity_line,
        "learner_email": learner_email,
        "show_identity_line": not is_preview and bool(learner_identity_line),
        "profile_fact_label": profile_fact_label,
        "profile_fact_value": profile_fact_value,
        "show_profile_fact": not is_preview and bool(profile_fact_value),
        "badge_name": badge_name,
        "signatory_name": signatory["name"],
        "signatory_title": signatory["title"],
        "theme": theme,
        "theme_style": build_theme_style(theme),
        "is_preview": is_preview,
        "show_identity": not is_preview and bool(learner_name),
        "show_certificate_number": not is_preview and bool(certificate_number),
        "state_label": "Preview" if is_preview else "Ready",
        "hero_copy": (
            "This default certificate becomes personalized after the course is successfully completed."
            if is_preview
            else f"{learner_name} completed this course on {issued_date}."
        ),
        "identity_placeholder": "Learner name appears after completion",
        "identity_line_placeholder": "Optional title and organization appear after completion",
        "issued_placeholder": "Completion date appears after finishing the course",
        "serial_placeholder": "Certificate ID is generated after completion",
        "profile_fact_placeholder": "Verified learner details appear after completion",
        "preview_notice": (
            "This is the default certificate design. Finish the course to unlock your personalized name, date, and certificate ID."
            if is_preview
            else ""
        ),
        "verification_copy": (
            "Default certificate preview only. Validation ID becomes available after successful completion."
            if is_preview
            else f"Validated in PLMS records under ID {certificate_number}"
        ),
    }


def build_certificate_view_model(certificate, issued_at=None):
    issued_on = issued_at or certificate.issued_at or timezone.now()
    profile = build_learner_certificate_profile(certificate.user)
    return _build_certificate_presentation(
        course=certificate.course,
        learner_name=profile["learner_name"],
        learner_identity_line=profile["learner_identity_line"],
        learner_email=profile["learner_email"],
        certificate_number=certificate.certificate_number,
        issued_on=issued_on,
        badge_name=certificate.badge.name if certificate.badge else "",
        is_preview=False,
    )
