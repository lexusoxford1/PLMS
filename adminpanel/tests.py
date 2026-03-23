from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from LMS.utils import award_course_completion
from courses.models import Course
from courses.models import Lesson
from quizzes.models import Quiz


class AdminPanelAccessTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username="adminuser",
            password="adminpass123",
            email="admin@example.com",
        )
        self.learner = user_model.objects.create_user(
            username="learner",
            password="learnerpass123",
            email="learner@example.com",
        )
        Course.objects.create(
            title="Python Basics",
            description="Intro course",
            overview="Overview",
            category=Course.CATEGORY_PYTHON,
        )

    def test_unauthenticated_user_is_redirected_to_admin_login(self):
        response = self.client.get(reverse("adminpanel:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("adminpanel:login"), response.url)

    def test_superuser_can_open_admin_dashboard(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("adminpanel:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Dashboard")

    def test_learner_cannot_open_admin_dashboard(self):
        self.client.force_login(self.learner)
        response = self.client.get(reverse("adminpanel:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))

    def test_dashboard_api_returns_metrics_for_staff(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("adminpanel:api_dashboard"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("metrics", payload)
        self.assertEqual(payload["metrics"]["total_courses"], 1)

    def test_dashboard_api_rejects_non_superuser(self):
        self.client.force_login(self.learner)
        response = self.client.get(
            reverse("adminpanel:api_dashboard"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["detail"],
            "Only Django superusers can access the Admin Panel.",
        )

    def test_admin_login_rejects_non_superuser_credentials(self):
        response = self.client.post(
            reverse("adminpanel:login"),
            {
                "username": "learner",
                "password": "learnerpass123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Only Django superusers can access the Admin Panel.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_admin_login_accepts_superuser_credentials(self):
        response = self.client.post(
            reverse("adminpanel:login"),
            {
                "username": "adminuser",
                "password": "adminpass123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("adminpanel:dashboard"))


class AdminPanelCourseApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username="builder",
            password="builderpass123",
            email="builder@example.com",
        )
        self.client.force_login(self.admin_user)

    def test_staff_can_create_course_via_api(self):
        response = self.client.post(
            reverse("adminpanel:api_courses"),
            {
                "title": "PHP Foundations",
                "description": "Learn PHP",
                "category": Course.CATEGORY_PHP,
                "overview": "Overview",
                "difficulty": Course.BEGINNER,
                "estimated_hours": 4,
                "is_published": "on",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Course.objects.filter(title="PHP Foundations").exists())


class AdminRoleSeparationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username="rootadmin",
            password="rootpass123",
            email="root@example.com",
        )
        self.learner = user_model.objects.create_user(
            username="studentuser",
            password="studentpass123",
            email="student@example.com",
        )
        self.course = Course.objects.create(
            title="C# Foundations",
            description="Introductory course",
            overview="Overview",
            category=Course.CATEGORY_CSHARP,
            is_published=True,
        )
        self.lesson = Lesson.objects.create(
            course=self.course,
            title="Getting Started",
            order=1,
            summary="Lesson summary",
            lecture_content="<p>Welcome</p>",
            is_published=True,
        )
        self.quiz = Quiz.objects.create(
            lesson=self.lesson,
            title="Checkpoint Quiz",
            instructions="Answer the checkpoint.",
            passing_score=70,
            is_published=True,
        )

    def test_superuser_is_redirected_away_from_learner_dashboard(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("adminpanel:dashboard"))

    def test_superuser_cannot_enroll_in_course(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(reverse("enroll_course", args=[self.course.slug]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("adminpanel:dashboard"))

    def test_superuser_cannot_open_learner_quiz_or_profile_routes(self):
        self.client.force_login(self.admin_user)

        quiz_response = self.client.get(reverse("quiz_detail", args=[self.quiz.id]))
        profile_response = self.client.get(reverse("profile"))
        badge_response = self.client.get(reverse("badge_list"))
        certificate_response = self.client.get(reverse("certificate_list"))

        self.assertEqual(quiz_response.status_code, 302)
        self.assertEqual(quiz_response.url, reverse("adminpanel:dashboard"))
        self.assertEqual(profile_response.status_code, 302)
        self.assertEqual(profile_response.url, reverse("adminpanel:dashboard"))
        self.assertEqual(badge_response.status_code, 302)
        self.assertEqual(badge_response.url, reverse("adminpanel:dashboard"))
        self.assertEqual(certificate_response.status_code, 302)
        self.assertEqual(certificate_response.url, reverse("adminpanel:dashboard"))

    def test_superuser_learner_api_requests_are_forbidden(self):
        self.client.force_login(self.admin_user)
        progress_response = self.client.get(reverse("api_course_progress", args=[self.course.slug]))
        activity_response = self.client.post(
            reverse("api_submit_lesson_activity", args=[self.course.slug, self.lesson.slug]),
            data={"response": "print('Hello')"},
        )

        self.assertEqual(progress_response.status_code, 403)
        self.assertEqual(
            progress_response.json()["detail"],
            "Admin accounts are reserved for system management and cannot access learner features.",
        )
        self.assertEqual(activity_response.status_code, 403)

    def test_course_completion_does_not_issue_certificate_for_superuser(self):
        certificate = award_course_completion(self.admin_user, self.course)
        self.assertIsNone(certificate)

    def test_admin_certificate_api_rejects_personal_issue_request(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("adminpanel:api_certificate_issue"),
            content_type="application/json",
            data=f'{{"user_id": {self.admin_user.id}, "course_id": {self.course.id}}}',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("course requirements", response.json()["errors"]["__all__"][0])

    def test_superuser_can_update_user_role_from_admin_panel(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("adminpanel:api_user_detail", args=[self.learner.id]),
            content_type="application/json",
            data='{"first_name":"Ada","last_name":"Learner","email":"student@example.com","role":"admin","is_active":true}',
        )

        self.assertEqual(response.status_code, 200)
        self.learner.refresh_from_db()
        self.assertTrue(self.learner.is_superuser)
        self.assertTrue(self.learner.is_staff)
        self.assertEqual(self.learner.role, self.learner.ADMIN)

    def test_superuser_cannot_remove_own_admin_access(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("adminpanel:api_user_detail", args=[self.admin_user.id]),
            content_type="application/json",
            data='{"first_name":"Root","last_name":"Admin","email":"root@example.com","role":"learner","is_active":true}',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("cannot remove your own admin access", response.json()["errors"]["role"][0].lower())


class PublicRegistrationTests(TestCase):
    def test_login_page_hides_public_register_call_to_action(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Create one here")
        self.assertContains(response, "Admin accounts are created manually")

    def test_public_registration_always_creates_learner_account(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newlearner",
                "first_name": "New",
                "last_name": "Learner",
                "email": "newlearner@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username="newlearner")
        self.assertEqual(user.role, user.LEARNER)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
