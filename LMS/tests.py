import shutil
import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from badges.models import Badge, UserBadge
from certificates.models import Certificate
from courses.models import Course, Enrollment, Lesson
from quizzes.models import Choice, Question, Quiz, QuizAttempt

from badges.services import build_user_achievement_summary

from .utils import can_access_lesson, course_completion_percentage, get_or_create_lesson_progress


class ProgressionFlowTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.media_root,
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        )
        self.settings_override.enable()

        self.user = get_user_model().objects.create_user(
            username="learner",
            password="testpass123",
            email="learner@example.com",
            first_name="Ada",
        )

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def create_quiz(self, lesson, title="Lesson Quiz"):
        quiz = Quiz.objects.create(lesson=lesson, title=title, passing_score=70)
        question = Question.objects.create(
            quiz=quiz,
            prompt="Which answer is correct?",
            order=1,
            points=1,
        )
        correct_choice = Choice.objects.create(
            question=question,
            text="Correct answer",
            is_correct=True,
            order=1,
        )
        Choice.objects.create(
            question=question,
            text="Incorrect answer",
            is_correct=False,
            order=2,
        )
        return quiz, question, correct_choice

    def test_next_lesson_stays_locked_until_quiz_is_passed(self):
        course = Course.objects.create(
            title="Python Foundations",
            description="Learn Python basics in order.",
            overview="Structured lessons for first-time programmers.",
        )
        lesson_one = Lesson.objects.create(
            course=course,
            title="Introduction",
            order=1,
            summary="Start here.",
            lecture_content="Welcome to Python.",
            activity_title="Warm-up",
            activity_instructions="Write a short explanation.",
        )
        lesson_two = Lesson.objects.create(
            course=course,
            title="Variables",
            order=2,
            summary="Continue after lesson one.",
            lecture_content="Variables store values.",
            activity_title="Practice",
            activity_instructions="Declare a variable.",
        )
        quiz, question, correct_choice = self.create_quiz(lesson_one, title="Intro Quiz")
        Enrollment.objects.create(user=self.user, course=course)

        self.assertTrue(can_access_lesson(self.user, lesson_one))
        self.assertFalse(can_access_lesson(self.user, lesson_two))

        progress = get_or_create_lesson_progress(self.user, lesson_one)
        progress.lecture_completed = True
        progress.activity_completed = True
        progress.save()

        QuizAttempt.objects.create(
            user=self.user,
            quiz=quiz,
            score=Decimal("0.00"),
            passed=False,
            submitted_answers={str(question.pk): "0"},
        )
        progress.refresh_from_db()
        self.assertFalse(progress.quiz_passed)
        self.assertIsNone(progress.completed_at)
        self.assertFalse(can_access_lesson(self.user, lesson_two))

        QuizAttempt.objects.create(
            user=self.user,
            quiz=quiz,
            score=Decimal("100.00"),
            passed=True,
            submitted_answers={str(question.pk): str(correct_choice.pk)},
        )
        progress.refresh_from_db()
        self.assertTrue(progress.quiz_passed)
        self.assertIsNotNone(progress.completed_at)
        self.assertTrue(can_access_lesson(self.user, lesson_two))

    def test_course_creation_prepares_two_badge_milestones(self):
        course = Course.objects.create(
            title="JavaScript Essentials",
            description="Learn JavaScript basics.",
            overview="A guided JavaScript path.",
        )

        self.assertEqual(course.badges.count(), 2)
        self.assertSetEqual(
            set(course.badges.values_list("award_type", flat=True)),
            {Badge.ENROLLMENT, Badge.COMPLETION},
        )

    def test_enrollment_awards_enrollment_badge(self):
        course = Course.objects.create(
            title="HTML Basics",
            description="Learn HTML structure.",
            overview="A simple course for markup fundamentals.",
        )

        Enrollment.objects.create(user=self.user, course=course)

        enrollment_award = UserBadge.objects.get(
            user=self.user,
            course=course,
            badge__award_type=Badge.ENROLLMENT,
        )
        self.assertEqual(enrollment_award.badge.course, course)
        self.assertFalse(enrollment_award.is_seen)
        self.assertTrue(
            UserBadge.objects.filter(user=self.user, badge__criteria_key="milestone:first-steps", course__isnull=True).exists()
        )

    def test_course_completion_generates_badge_certificate_and_email(self):
        course = Course.objects.create(
            title="Django Essentials",
            description="Build a complete beginner-friendly Django app.",
            overview="Finish one guided lesson and claim the rewards.",
        )
        lesson = Lesson.objects.create(
            course=course,
            title="Routing and Views",
            order=1,
            summary="Understand URLs and views.",
            lecture_content="Django routes requests with URL patterns.",
            activity_title="Code Reflection",
            activity_instructions="Explain how a URL reaches a view.",
        )
        quiz, question, correct_choice = self.create_quiz(lesson, title="Final Checkpoint")
        enrollment = Enrollment.objects.create(user=self.user, course=course)

        progress = get_or_create_lesson_progress(self.user, lesson)
        progress.lecture_completed = True
        progress.activity_completed = True
        progress.save()

        QuizAttempt.objects.create(
            user=self.user,
            quiz=quiz,
            score=Decimal("100.00"),
            passed=True,
            submitted_answers={str(question.pk): str(correct_choice.pk)},
        )

        enrollment.refresh_from_db()
        self.assertIsNotNone(enrollment.completed_at)
        self.assertEqual(course_completion_percentage(self.user, course), 100)
        self.assertEqual(UserBadge.objects.filter(user=self.user, course=course).count(), 2)
        self.assertTrue(
            UserBadge.objects.filter(user=self.user, course=course, badge__award_type=Badge.ENROLLMENT).exists()
        )
        self.assertTrue(
            UserBadge.objects.filter(user=self.user, course=course, badge__award_type=Badge.COMPLETION).exists()
        )

        certificate = Certificate.objects.get(user=self.user, course=course)
        self.assertIsNotNone(certificate.issued_at)
        self.assertTrue(certificate.file.name.endswith(".pdf"))

        certificate.file.open("rb")
        self.assertEqual(certificate.file.read(5), b"%PDF-")
        certificate.file.close()

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Django Essentials", mail.outbox[0].subject)

    def test_passing_final_quiz_redirects_to_certificate_view(self):
        course = Course.objects.create(
            title="C Sharp Basics",
            description="Complete the final quiz to earn a certificate.",
            overview="A short path for certificate redirect coverage.",
        )
        lesson = Lesson.objects.create(
            course=course,
            title="Finish Line",
            order=1,
            summary="Wrap up the lesson.",
            lecture_content="The final checkpoint unlocks the certificate.",
            activity_title="Reflection",
            activity_instructions="Share what you learned.",
        )
        quiz, question, correct_choice = self.create_quiz(lesson, title="Completion Quiz")
        Enrollment.objects.create(user=self.user, course=course)

        progress = get_or_create_lesson_progress(self.user, lesson)
        progress.lecture_completed = True
        progress.activity_completed = True
        progress.save()

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("quiz_detail", args=[quiz.pk]),
            {question.field_name: str(correct_choice.pk)},
        )

        certificate = Certificate.objects.get(user=self.user, course=course)
        self.assertRedirects(response, reverse("certificate_detail", args=[certificate.pk]))

    def test_course_detail_shows_default_certificate_preview_before_completion(self):
        course = Course.objects.create(
            title="Preview Ready Python",
            description="A course with a visible default certificate preview.",
            overview="Preview the certificate before finishing.",
        )
        Enrollment.objects.create(user=self.user, course=course)

        self.client.force_login(self.user)
        response = self.client.get(reverse("course_detail", args=[course.slug]))

        self.assertContains(response, "Learner name appears after completion")
        self.assertContains(response, "Certificate ID is generated after completion")
        self.assertContains(response, "default certificate design")

    def test_certificate_list_shows_preview_cards_for_incomplete_courses(self):
        course = Course.objects.create(
            title="Preview Card Course",
            description="Shows preview cards on the certificates page.",
            overview="Incomplete courses stay in preview mode.",
        )
        Enrollment.objects.create(user=self.user, course=course)

        self.client.force_login(self.user)
        response = self.client.get(reverse("certificate_list"))

        self.assertContains(response, "Default Certificate Preview")
        self.assertContains(response, "Default design only for now")
        self.assertContains(response, "No ID yet")

    def test_perfect_quiz_score_unlocks_milestones_and_levels_up_user(self):
        course = Course.objects.create(
            title="Java Foundations",
            description="Finish one lesson and one quiz.",
            overview="A short path for milestone testing.",
        )
        lesson = Lesson.objects.create(
            course=course,
            title="Basics",
            order=1,
            summary="Start here.",
            lecture_content="A short lecture.",
            activity_title="Reflection",
            activity_instructions="Write a short answer.",
        )
        quiz, question, correct_choice = self.create_quiz(lesson, title="Checkpoint")
        Enrollment.objects.create(user=self.user, course=course)

        progress = get_or_create_lesson_progress(self.user, lesson)
        progress.lecture_completed = True
        progress.activity_completed = True
        progress.save()

        QuizAttempt.objects.create(
            user=self.user,
            quiz=quiz,
            score=Decimal("100.00"),
            passed=True,
            submitted_answers={str(question.pk): str(correct_choice.pk)},
        )

        self.assertTrue(
            UserBadge.objects.filter(user=self.user, badge__criteria_key="milestone:perfect-pulse").exists()
        )
        self.assertTrue(
            UserBadge.objects.filter(user=self.user, badge__criteria_key="milestone:graduation-glow").exists()
        )

        summary = build_user_achievement_summary(self.user)
        self.assertEqual(summary["total_xp"], 480)
        self.assertEqual(summary["level"], 4)
