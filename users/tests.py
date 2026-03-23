import shutil
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from certificates.models import Certificate
from certificates.presentation import build_certificate_view_model
from courses.models import Course


class ProfileDashboardTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_root)
        self.settings_override.enable()

        self.user = get_user_model().objects.create_user(
            username="profileuser",
            password="testpass123",
            email="profile@example.com",
            first_name="Profile",
            last_name="User",
        )
        self.course = Course.objects.create(
            title="Profile Ready Course",
            description="A short course used for profile dashboard coverage.",
            overview="Used to verify certificate personalization.",
        )
        self.certificate = Certificate.objects.create(user=self.user, course=self.course)

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_certificate_view_model_uses_certificate_profile_fields(self):
        self.user.title = "Senior Python Learner"
        self.user.organization = "PLMS Lab"
        self.user.certificate_name = "Grace Hopper"
        self.user.save()

        presentation = build_certificate_view_model(self.certificate)

        self.assertEqual(presentation["learner_name"], "Grace Hopper")
        self.assertEqual(presentation["learner_identity_line"], "Senior Python Learner | PLMS Lab")
        self.assertEqual(presentation["learner_email"], "profile@example.com")
        self.assertEqual(presentation["profile_fact_label"], "Verified Email")
        self.assertEqual(presentation["profile_fact_value"], "profile@example.com")

    def test_profile_update_refreshes_certificate_artifacts_and_profile_fields(self):
        self.client.force_login(self.user)

        with patch("certificates.models.generate_certificate_pdf", return_value=b"%PDF-1.4 profile-sync"):
            response = self.client.post(
                reverse("profile"),
                {
                    "action": "profile",
                    "first_name": "Grace",
                    "last_name": "Hopper",
                    "title": "Lead LMS Engineer",
                    "organization": "PLMS Academy",
                    "email": "grace@example.com",
                    "phone_number": "+63 900 000 0000",
                    "certificate_name": "Grace Brewster Hopper",
                    "bio": "Building learner-first dashboards.",
                },
            )

        self.assertRedirects(response, f"{reverse('profile')}?panel=settings")
        self.user.refresh_from_db()
        self.certificate.refresh_from_db()

        self.assertEqual(self.user.first_name, "Grace")
        self.assertEqual(self.user.last_name, "Hopper")
        self.assertEqual(self.user.title, "Lead LMS Engineer")
        self.assertEqual(self.user.organization, "PLMS Academy")
        self.assertEqual(self.user.email, "grace@example.com")
        self.assertEqual(self.user.certificate_name, "Grace Brewster Hopper")
        self.assertTrue(self.certificate.file.name.endswith(".pdf"))

        with patch("certificates.models.generate_certificate_pdf", return_value=b"%PDF-1.4 preview"):
            detail_response = self.client.get(reverse("certificate_detail", args=[self.certificate.pk]))

        self.assertContains(detail_response, "Grace Brewster Hopper")
        self.assertContains(detail_response, "Lead LMS Engineer | PLMS Academy")
        self.assertContains(detail_response, "grace@example.com")

    def test_profile_password_change_keeps_user_logged_in(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("profile"),
            {
                "action": "password",
                "old_password": "testpass123",
                "new_password1": "updatedpass12345",
                "new_password2": "updatedpass12345",
            },
        )

        self.assertRedirects(response, f"{reverse('profile')}?panel=security")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("updatedpass12345"))

        follow_up = self.client.get(reverse("profile"))
        self.assertEqual(follow_up.status_code, 200)


class RegistrationTests(TestCase):
    def test_register_view_logs_in_new_learner_with_explicit_backend(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "freshlearner",
                "first_name": "Fresh",
                "last_name": "Learner",
                "email": "fresh@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("dashboard"))
        user = get_user_model().objects.get(username="freshlearner")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)
        self.assertEqual(user.role, user.LEARNER)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
