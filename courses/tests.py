import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from LMS.utils import can_access_lesson, get_or_create_lesson_progress

from .activity_service import build_activity_concept_review
from .activity_validation import validate_activity_submission
from .code_runner.process import minimal_env
from .code_runner.schemas import CodeExecutionResult
from .models import Course, Enrollment, Lesson


class ProgrammingCourseSeedTests(TestCase):
    def test_seed_programming_courses_creates_three_progressive_courses(self):
        call_command("seed_programming_courses")

        expected_titles = {
            "Python Programming Foundations",
            "PHP Programming Foundations",
            "C# Programming Foundations",
        }
        self.assertEqual(set(Course.objects.values_list("title", flat=True)), expected_titles)

        for course in Course.objects.prefetch_related("lessons__quiz__questions"):
            lessons = list(course.lessons.order_by("order"))
            self.assertEqual(len(lessons), 6)
            self.assertTrue(all(lesson.has_activity for lesson in lessons))
            self.assertTrue(all(lesson.has_activity_validation for lesson in lessons))
            self.assertFalse(any(lesson.has_quiz for lesson in lessons[:-1]))
            self.assertTrue(lessons[-1].has_quiz)
            self.assertGreaterEqual(lessons[-1].quiz.questions.count(), 6)
            self.assertIn("<pre><code>", lessons[0].lecture_content)

        csharp_course = Course.objects.get(slug="csharp-programming-foundations")
        self.assertTrue(
            all(lesson.activity_validation_rules.get("validator") == "code_runner" for lesson in csharp_course.lessons.all())
        )
        self.assertTrue(
            all(lesson.activity_validation_rules.get("language") == "csharp" for lesson in csharp_course.lessons.all())
        )

        python_course = Course.objects.get(slug="python-programming-foundations")
        self.assertTrue(
            all(lesson.activity_validation_rules.get("validator") == "code_runner" for lesson in python_course.lessons.all())
        )
        self.assertTrue(
            all(lesson.activity_validation_rules.get("language") == "python" for lesson in python_course.lessons.all())
        )
        self.assertTrue(
            all(
                lesson.activity_title.startswith(f"Activity {lesson.order}:")
                for lesson in python_course.lessons.order_by("order")
            )
        )

        php_course = Course.objects.get(slug="php-programming-foundations")
        self.assertTrue(
            all(lesson.activity_validation_rules.get("validator") == "code_runner" for lesson in php_course.lessons.all())
        )
        self.assertTrue(
            all(lesson.activity_validation_rules.get("language") == "php" for lesson in php_course.lessons.all())
        )
        self.assertTrue(
            all(
                lesson.activity_title.startswith(f"Activity {lesson.order}:")
                for lesson in php_course.lessons.order_by("order")
            )
        )
        self.assertTrue(
            all(
                lesson.activity_validation_rules.get("accept_alternative_solutions") is True
                for lesson in php_course.lessons.all()
            )
        )

        call_command("seed_programming_courses")
        self.assertEqual(Course.objects.count(), 3)
        self.assertEqual(sum(course.lessons.count() for course in Course.objects.all()), 18)


class ActivityValidationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="learner",
            password="testpass123",
            email="learner@example.com",
        )
        self.course = Course.objects.create(
            title="Validation Course",
            description="Test the activity validator.",
            overview="A short validation flow.",
        )
        self.lesson_one = Lesson.objects.create(
            course=self.course,
            title="Lesson One",
            order=1,
            summary="Practice output.",
            lecture_content="<p>Use print().</p>",
            activity_title="Output Activity",
            activity_instructions="<p>Write three print statements.</p>",
            activity_hint="Use print() three times.",
            activity_validation_rules={
                "required_patterns": [
                    {"pattern": r"\bprint\s*\(", "description": "three print() statements", "count": 3},
                ],
                "success_explanation": "You used print() enough times to complete the activity.",
                "failure_hint": "Add more print() statements and try again.",
            },
        )
        self.lesson_two = Lesson.objects.create(
            course=self.course,
            title="Lesson Two",
            order=2,
            summary="Unlocked only after validation.",
            lecture_content="<p>Next lesson.</p>",
        )
        Enrollment.objects.create(user=self.user, course=self.course)
        self.client.login(username="learner", password="testpass123")

    def test_incorrect_activity_keeps_next_lesson_locked(self):
        progress = get_or_create_lesson_progress(self.user, self.lesson_one)
        progress.lecture_completed = True
        progress.save()

        response = self.client.post(
            reverse("submit_activity", args=[self.course.slug, self.lesson_one.slug]),
            {"response": 'print("hello")'},
            follow=True,
        )
        progress.refresh_from_db()

        self.assertFalse(progress.activity_completed)
        self.assertEqual(progress.activity_status, progress.INCORRECT)
        self.assertEqual(progress.activity_attempts, 1)
        self.assertIn("Incorrect answer. Please review the lesson and try again.", response.content.decode())
        self.assertIn("Add more print() statements and try again.", response.content.decode())
        self.assertFalse(can_access_lesson(self.user, self.lesson_two))

    def test_correct_activity_unlocks_the_next_lesson(self):
        progress = get_or_create_lesson_progress(self.user, self.lesson_one)
        progress.lecture_completed = True
        progress.save()

        response = self.client.post(
            reverse("submit_activity", args=[self.course.slug, self.lesson_one.slug]),
            {"response": 'print("a")\nprint("b")\nprint("c")'},
            follow=True,
        )
        progress.refresh_from_db()

        self.assertTrue(progress.activity_completed)
        self.assertEqual(progress.activity_status, progress.CORRECT)
        self.assertEqual(progress.activity_attempts, 1)
        self.assertIn("Correct answer. You have successfully completed this activity.", response.content.decode())
        self.assertIn("You used print() enough times to complete the activity.", response.content.decode())
        self.assertTrue(can_access_lesson(self.user, self.lesson_two))


class CodeRunnerActivityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="coder",
            password="testpass123",
            email="coder@example.com",
        )
        self.course = Course.objects.create(
            title="Code Runner Course",
            description="Test the multi-language code runner.",
            overview="A short course for code runner validation.",
        )
        self.lesson_one = Lesson.objects.create(
            course=self.course,
            title="Python Output Check",
            order=1,
            summary="Run deterministic Python code.",
            lecture_content="<p>Print a greeting.</p>",
            activity_title="Greeting Activity",
            activity_instructions="<p>Print exactly Hello, learner!</p>",
            activity_hint="Use one print() statement with the exact greeting.",
            activity_validation_rules={
                "validator": "code_runner",
                "language": "python",
                "expected_output": "Hello, learner!",
                "success_explanation": "Your Python code produced the expected output.",
                "failure_hint": "Print Hello, learner! exactly.",
            },
        )
        self.lesson_two = Lesson.objects.create(
            course=self.course,
            title="Next Lesson",
            order=2,
            summary="Unlocks after the coding activity.",
            lecture_content="<p>Keep learning.</p>",
        )
        Enrollment.objects.create(user=self.user, course=self.course)
        self.client.login(username="coder", password="testpass123")

    def _runner_settings(self):
        return {
            **settings.CODE_RUNNER,
            "EXECUTION_ROOT": Path(settings.BASE_DIR) / ".test_code_runner",
            "PYTHON_CMD": sys.executable,
        }

    def test_python_code_runner_unlocks_next_lesson_on_correct_output(self):
        progress = get_or_create_lesson_progress(self.user, self.lesson_one)
        progress.lecture_completed = True
        progress.save()

        with self.settings(CODE_RUNNER=self._runner_settings()):
            response = self.client.post(
                reverse("submit_activity", args=[self.course.slug, self.lesson_one.slug]),
                {"response": 'print("Hello, learner!")'},
                follow=True,
            )

        progress.refresh_from_db()
        self.assertTrue(progress.activity_completed)
        self.assertEqual(progress.activity_status, progress.CORRECT)
        self.assertEqual(progress.activity_result_data["execution_status"], "success")
        self.assertEqual(progress.activity_result_data["validation_result"], "correct")
        self.assertIn("Hello, learner!", progress.activity_result_data["program_output"])
        self.assertIn("Your Python code produced the expected output.", response.content.decode())
        self.assertTrue(can_access_lesson(self.user, self.lesson_two))

    def test_python_runtime_error_returns_beginner_friendly_feedback(self):
        progress = get_or_create_lesson_progress(self.user, self.lesson_one)
        progress.lecture_completed = True
        progress.save()

        with self.settings(CODE_RUNNER=self._runner_settings()):
            self.client.post(
                reverse("submit_activity", args=[self.course.slug, self.lesson_one.slug]),
                {"response": "print(1 / 0)"},
                follow=True,
            )

        progress.refresh_from_db()
        self.assertFalse(progress.activity_completed)
        self.assertEqual(progress.activity_result_data["execution_status"], "error")
        self.assertEqual(progress.activity_result_data["validation_result"], "incorrect")
        self.assertIn("divide by zero", progress.activity_feedback_body.lower())
        self.assertFalse(can_access_lesson(self.user, self.lesson_two))

    def test_api_submission_returns_structured_activity_payload(self):
        progress = get_or_create_lesson_progress(self.user, self.lesson_one)
        progress.lecture_completed = True
        progress.save()

        with self.settings(CODE_RUNNER=self._runner_settings()):
            response = self.client.post(
                reverse("api_submit_lesson_activity", args=[self.course.slug, self.lesson_one.slug]),
                data=json.dumps({"code": 'print("Hello, learner!")'}),
                content_type="application/json",
            )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["activity"]["execution_status"], "success")
        self.assertEqual(payload["activity"]["validation_result"], "correct")
        self.assertEqual(payload["notification"]["level"], "success")
        self.assertTrue(payload["progress"]["next_lesson_unlocked"])

    def test_python_lessons_use_the_dedicated_python_runner_service(self):
        lesson = Lesson.objects.create(
            course=self.course,
            title="Python Service Dispatch",
            order=9,
            summary="Dispatch through the dedicated Python runner.",
            lecture_content="<p>Run code.</p>",
            activity_title="Python service",
            activity_instructions="<p>Print the expected greeting.</p>",
            activity_validation_rules={
                "validator": "code_runner",
                "language": "python",
                "expected_output": "Hello from Python",
            },
        )

        sentinel = object()
        with patch("courses.code_runner.validation.validate_python_activity_submission", return_value=sentinel) as mocked:
            result = validate_activity_submission(lesson, 'print("Hello from Python")')

        mocked.assert_called_once_with(lesson, 'print("Hello from Python")')
        self.assertIs(result, sentinel)

    def test_php_lessons_use_the_dedicated_php_runner_service(self):
        lesson = Lesson.objects.create(
            course=self.course,
            title="PHP Service Dispatch",
            order=10,
            summary="Dispatch through the dedicated PHP runner.",
            lecture_content="<p>Run code.</p>",
            activity_title="PHP service",
            activity_instructions="<p>Print the expected greeting.</p>",
            activity_validation_rules={
                "validator": "code_runner",
                "language": "php",
                "expected_output": "Hello from PHP",
            },
        )

        sentinel = object()
        with patch("courses.code_runner.validation.validate_php_activity_submission", return_value=sentinel) as mocked:
            result = validate_activity_submission(lesson, "<?php\necho 'Hello from PHP';")

        mocked.assert_called_once_with(lesson, "<?php\necho 'Hello from PHP';")
        self.assertIs(result, sentinel)

    def test_php_and_csharp_lessons_use_the_code_runner_validation_path(self):
        language_expectations = {
            "php": ("<?php\necho 'Hello from PHP';", "Hello from PHP"),
            "csharp": ('using System;\nclass Program { static void Main() { Console.WriteLine("Hello from C#"); } }', "Hello from C#"),
        }

        for order, (language, (response_text, expected_output)) in enumerate(language_expectations.items(), start=3):
            lesson = Lesson.objects.create(
                course=self.course,
                title=f"{language.title()} Activity",
                order=order,
                summary=f"Validate {language} code.",
                lecture_content="<p>Run code.</p>",
                activity_title=f"{language.title()} runner",
                activity_instructions="<p>Print the expected greeting.</p>",
                activity_validation_rules={
                    "validator": "code_runner",
                    "language": language,
                    "expected_output": expected_output,
                },
            )

            mocked_result = CodeExecutionResult(
                language=language,
                execution_status="success",
                program_output=f"{expected_output}\n",
                execution_time_ms=12,
            )
            with self.subTest(language=language):
                patch_target = (
                    "courses.csharp_runner.service.compile_and_execute_csharp"
                    if language == "csharp"
                    else "courses.php_runner.service.execute_code"
                )
                with patch(patch_target, return_value=mocked_result):
                    result = validate_activity_submission(lesson, response_text)

                self.assertTrue(result.is_correct)
                self.assertEqual(result.language, language)
                self.assertTrue(result.used_code_runner)
                self.assertEqual(result.validation_result, "correct")

    def test_php_accepts_alternative_solution_structure_when_output_is_correct(self):
        lesson = Lesson.objects.create(
            course=self.course,
            title="PHP Output-Focused Activity",
            order=11,
            summary="Accept different PHP solution styles.",
            lecture_content="<p>Run code.</p>",
            activity_title="PHP output-focused runner",
            activity_instructions="<p>Print the expected greeting.</p>",
            activity_validation_rules={
                "validator": "code_runner",
                "language": "php",
                "expected_output_contains": ["Hello from PHP"],
                "required_patterns": [
                    {"pattern": r"\becho\b", "description": "echo statements", "count": 2},
                ],
                "accept_alternative_solutions": True,
            },
        )

        mocked_result = CodeExecutionResult(
            language="php",
            execution_status="success",
            program_output="Hello from PHP\n",
            execution_time_ms=12,
        )
        with patch("courses.php_runner.service.execute_code", return_value=mocked_result):
            result = validate_activity_submission(lesson, '<?php\nprint "Hello from PHP\\n";')

        self.assertTrue(result.is_correct)
        self.assertEqual(result.validation_result, "correct")
        self.assertEqual(result.language, "php")

    def test_legacy_php_variables_activity_accepts_br_separated_output(self):
        legacy_course = Course.objects.create(
            title="PHP Programming Foundations",
            slug="php-programming-foundations",
            description="Use seeded PHP runner rules for legacy lessons.",
            overview="Render only.",
        )
        lesson = Lesson.objects.create(
            course=legacy_course,
            title="Variables and Data Types",
            order=2,
            slug="php-variables-and-data-types",
            summary="Legacy PHP variables lesson.",
            lecture_content="<p>Lecture content.</p>",
            activity_title="Activity 2: Learner Profile Variables",
            activity_instructions="<p>Create learner profile output.</p>",
            activity_validation_rules={
                "required_patterns": [
                    {"pattern": r"\$favoriteFeature\b", "description": "the $favoriteFeature variable", "count": 1},
                ],
                "success_explanation": "Legacy rules.",
                "failure_hint": "Legacy hint.",
            },
        )

        mocked_result = CodeExecutionResult(
            language="php",
            execution_status="success",
            program_output="Name: Lia<br>Age: 20<br>Favorite Language Feature: Loops",
            execution_time_ms=12,
        )
        with patch("courses.php_runner.service.execute_code", return_value=mocked_result):
            result = validate_activity_submission(
                lesson,
                '<?php\n$name = "Lia";\n$age = 20;\n$favoriteFeature = "Loops";\nprint "Name: " . $name;\nprint "<br>";\nprint "Age: " . $age;\nprint "<br>";\nprint "Favorite Language Feature: " . $favoriteFeature;',
            )

        self.assertTrue(result.is_correct)
        self.assertEqual(result.validation_result, "correct")
        self.assertEqual(result.language, "php")

    def test_csharp_blocked_construct_is_rejected_before_execution(self):
        lesson = Lesson.objects.create(
            course=self.course,
            title="C# Security Activity",
            order=10,
            summary="Reject dangerous APIs.",
            lecture_content="<p>Stay inside the sandbox.</p>",
            activity_title="Secure C#",
            activity_instructions="<p>Do not use file APIs.</p>",
            activity_validation_rules={
                "validator": "code_runner",
                "language": "csharp",
                "expected_output": "Safe output",
            },
        )

        result = validate_activity_submission(
            lesson,
            "using System.IO;\nusing System;\nclass Program { static void Main() { Console.WriteLine(\"Safe output\"); } }",
        )

        self.assertFalse(result.is_correct)
        self.assertEqual(result.execution_status, "error")
        self.assertIn("blocks C#", result.explanation)

    def test_csharp_compile_error_includes_backend_notification_metadata(self):
        lesson = Lesson.objects.create(
            course=self.course,
            title="C# Compiler Notification",
            order=11,
            summary="Return compiler metadata.",
            lecture_content="<p>Compile the code.</p>",
            activity_title="Compiler feedback",
            activity_instructions="<p>Trigger a compile error.</p>",
            activity_validation_rules={
                "validator": "code_runner",
                "language": "csharp",
                "expected_output": None,
            },
        )

        mocked_result = CodeExecutionResult(
            language="csharp",
            execution_status="error",
            errors="Program.cs(7,21): error CS1002: ; expected",
            execution_time_ms=15,
            details={"stage": "compile"},
        )
        with patch("courses.csharp_runner.service.compile_and_execute_csharp", return_value=mocked_result):
            result = validate_activity_submission(
                lesson,
                'using System;\nclass Program { static void Main() { Console.WriteLine("Hello") } }',
            )

        self.assertEqual(result.notification["kind"], "csharp_compile_error")
        self.assertEqual(result.notification["location"]["line"], 7)
        self.assertEqual(result.notification["location"]["column"], 21)
        self.assertIn("compiler", result.notification["message"].lower())

    def test_csharp_environment_issue_returns_clear_setup_notification(self):
        lesson = Lesson.objects.create(
            course=self.course,
            title="C# Compiler Environment Notification",
            order=12,
            summary="Return setup metadata.",
            lecture_content="<p>Compile the code.</p>",
            activity_title="Compiler environment feedback",
            activity_instructions="<p>Trigger an environment error.</p>",
            activity_validation_rules={
                "validator": "code_runner",
                "language": "csharp",
                "expected_output": None,
            },
        )

        mocked_result = CodeExecutionResult(
            language="csharp",
            execution_status="error",
            errors=(
                "An issue was encountered verifying workloads.\n"
                "error : The type initializer for 'NuGet.Configuration.ConfigurationDefaults' threw an exception.\n"
                "error : Value cannot be null. (Parameter 'path1')"
            ),
            execution_time_ms=17,
            details={"stage": "compile", "compiler_stage": "restore", "environment_issue": "workload_verification"},
        )
        with patch("courses.csharp_runner.service.compile_and_execute_csharp", return_value=mocked_result):
            result = validate_activity_submission(
                lesson,
                'using System;\nclass Program { static void Main() { Console.WriteLine("Hello"); } }',
            )

        self.assertEqual(result.notification["kind"], "csharp_compiler_environment_error")
        self.assertIn("setup", result.notification["title"].lower())
        self.assertIn("workload", result.notification["message"].lower())

    def test_csharp_lesson_detail_renders_compiler_workspace(self):
        render_course = Course.objects.create(
            title="C# UI Course",
            description="Render the dedicated compiler UI.",
            overview="Render only.",
        )
        Enrollment.objects.create(user=self.user, course=render_course)
        lesson = Lesson.objects.create(
            course=render_course,
            title="C# Lesson UI",
            order=1,
            slug="csharp-lesson-ui",
            summary="Render the C# compiler page.",
            lecture_content="<p>Lecture content.</p>",
            activity_title="C# Workspace",
            activity_instructions="<p>Compile your code.</p>",
            activity_validation_rules={
                "validator": "code_runner",
                "language": "csharp",
                "starter_code": "using System;",
            },
        )

        response = self.client.get(reverse("lesson_detail", args=[render_course.slug, lesson.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dedicated C# Compiler")
        self.assertContains(response, "Run Code")
        self.assertContains(response, "Quick Start")
        self.assertContains(response, "Reset Editor")
        self.assertNotContains(response, "View Results")

    def test_python_lesson_detail_renders_dedicated_runner_workspace(self):
        render_course = Course.objects.create(
            title="Python UI Course",
            description="Render the dedicated Python runner UI.",
            overview="Render only.",
        )
        Enrollment.objects.create(user=self.user, course=render_course)
        lesson = Lesson.objects.create(
            course=render_course,
            title="Python Lesson UI",
            order=1,
            slug="python-lesson-ui",
            summary="Render the Python runner page.",
            lecture_content="<p>Lecture content.</p>",
            activity_title="Python Workspace",
            activity_instructions="<p>Run your code.</p>",
            activity_validation_rules={
                "validator": "code_runner",
                "language": "python",
                "starter_code": 'print("Hello, Python")',
            },
        )

        response = self.client.get(reverse("lesson_detail", args=[render_course.slug, lesson.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dedicated Python Compiler")
        self.assertContains(response, "Run Code")
        self.assertContains(response, "Compiler")
        self.assertContains(response, "Quick Start")
        self.assertContains(response, "Reset Editor")
        self.assertNotContains(response, "View Results")
        self.assertContains(response, "main.py")

    def test_php_lesson_detail_renders_dedicated_runner_workspace(self):
        render_course = Course.objects.create(
            title="PHP UI Course",
            description="Render the dedicated PHP runner UI.",
            overview="Render only.",
        )
        Enrollment.objects.create(user=self.user, course=render_course)
        lesson = Lesson.objects.create(
            course=render_course,
            title="PHP Lesson UI",
            order=1,
            slug="php-lesson-ui",
            summary="Render the PHP runner page.",
            lecture_content="<p>Lecture content.</p>",
            activity_title="PHP Workspace",
            activity_instructions="<p>Run your code.</p>",
            activity_validation_rules={
                "validator": "code_runner",
                "language": "php",
                "starter_code": '<?php\necho "Hello, PHP";',
            },
        )

        response = self.client.get(reverse("lesson_detail", args=[render_course.slug, lesson.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dedicated PHP Compiler")
        self.assertContains(response, "Run Code")
        self.assertContains(response, "Compiler")
        self.assertContains(response, "Quick Start")
        self.assertContains(response, "Reset Editor")
        self.assertNotContains(response, "View Results")
        self.assertContains(response, "main.php")

    def test_legacy_python_activity_still_renders_dedicated_compiler_workspace(self):
        render_course = Course.objects.create(
            title="Python Programming Foundations",
            slug="python-programming-foundations",
            description="Render the Python compiler UI from legacy lesson data.",
            overview="Render only.",
        )
        Enrollment.objects.create(user=self.user, course=render_course)
        lesson = Lesson.objects.create(
            course=render_course,
            title="Getting Started with Python",
            order=1,
            slug="getting-started-with-python",
            summary="Render the Python compiler page from old saved rules.",
            lecture_content="<p>Lecture content.</p>",
            activity_title="Activity 1: Friendly Program Output",
            activity_instructions="<p>Write a short Python program.</p>",
            activity_validation_rules={
                "required_patterns": [
                    {"pattern": r"\bprint\s*\(", "description": "three print() statements", "count": 3},
                ],
                "success_explanation": "Legacy rules.",
                "failure_hint": "Legacy hint.",
            },
        )

        response = self.client.get(reverse("lesson_detail", args=[render_course.slug, lesson.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dedicated Python Compiler")
        self.assertContains(response, "main.py")
        self.assertContains(response, "# Write your print() statements below")
        self.assertContains(response, "Run Code")

    def test_legacy_php_activity_still_renders_dedicated_compiler_workspace(self):
        render_course = Course.objects.create(
            title="PHP Programming Foundations",
            slug="php-programming-foundations",
            description="Render the PHP compiler UI from legacy lesson data.",
            overview="Render only.",
        )
        Enrollment.objects.create(user=self.user, course=render_course)
        lesson = Lesson.objects.create(
            course=render_course,
            title="Getting Started with PHP",
            order=1,
            slug="getting-started-with-php",
            summary="Render the PHP compiler page from old saved rules.",
            lecture_content="<p>Lecture content.</p>",
            activity_title="Activity 1: Basic PHP Output",
            activity_instructions="<p>Write a short PHP program.</p>",
            activity_validation_rules={
                "required_patterns": [
                    {"pattern": r"\becho\b", "description": "three echo statements", "count": 3},
                ],
                "success_explanation": "Legacy rules.",
                "failure_hint": "Legacy hint.",
            },
        )

        response = self.client.get(reverse("lesson_detail", args=[render_course.slug, lesson.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dedicated PHP Compiler")
        self.assertContains(response, "main.php")
        self.assertContains(response, "// Write your echo statements here")
        self.assertContains(response, "Run Code")

    def test_legacy_python_activity_uses_effective_runner_rules_when_submitting_code(self):
        legacy_course = Course.objects.create(
            title="Python Programming Foundations",
            slug="python-programming-foundations",
            description="Use seeded Python runner rules for legacy lessons.",
            overview="Render only.",
        )
        lesson = Lesson.objects.create(
            course=legacy_course,
            title="Getting Started with Python",
            order=1,
            slug="getting-started-with-python",
            summary="Legacy Python lesson.",
            lecture_content="<p>Lecture content.</p>",
            activity_title="Activity 1: Friendly Program Output",
            activity_instructions="<p>Write a short Python program.</p>",
            activity_validation_rules={
                "required_patterns": [
                    {"pattern": r"\bprint\s*\(", "description": "three print() statements", "count": 3},
                ],
                "success_explanation": "Legacy rules.",
                "failure_hint": "Legacy hint.",
            },
        )

        mocked_result = CodeExecutionResult(
            language="python",
            execution_status="success",
            program_output="Ada\nI am learning Python\nKeep going\n",
            execution_time_ms=12,
        )
        with patch("courses.python_runner.service.execute_code", return_value=mocked_result):
            result = validate_activity_submission(
                lesson,
                'print("Ada")\nprint("I am learning Python")\nprint("Keep going")',
            )

        self.assertTrue(result.is_correct)
        self.assertEqual(result.language, "python")
        self.assertNotIn("supported language configuration", result.explanation.lower())

    def test_legacy_php_activity_uses_effective_runner_rules_when_submitting_code(self):
        legacy_course = Course.objects.create(
            title="PHP Programming Foundations",
            slug="php-programming-foundations",
            description="Use seeded PHP runner rules for legacy lessons.",
            overview="Render only.",
        )
        lesson = Lesson.objects.create(
            course=legacy_course,
            title="Getting Started with PHP",
            order=1,
            slug="getting-started-with-php",
            summary="Legacy PHP lesson.",
            lecture_content="<p>Lecture content.</p>",
            activity_title="Activity 1: Basic PHP Output",
            activity_instructions="<p>Write a short PHP program.</p>",
            activity_validation_rules={
                "required_patterns": [
                    {"pattern": r"\becho\b", "description": "three echo statements", "count": 3},
                ],
                "success_explanation": "Legacy rules.",
                "failure_hint": "Legacy hint.",
            },
        )

        mocked_result = CodeExecutionResult(
            language="php",
            execution_status="success",
            program_output="Ada\nI am learning PHP\nKeep going\n",
            execution_time_ms=12,
        )
        with patch("courses.php_runner.service.execute_code", return_value=mocked_result):
            result = validate_activity_submission(
                lesson,
                '<?php\nprint "Ada\\nI am learning PHP\\nKeep going\\n";',
            )

        self.assertTrue(result.is_correct)
        self.assertEqual(result.language, "php")
        self.assertNotIn("supported language configuration", result.explanation.lower())

    def test_build_activity_concept_review_returns_result_evaluator_review(self):
        lesson = Lesson(
            title="Conditional Statements",
            slug="csharp-conditional-statements",
            activity_instructions="<p>Complete the activity.</p>",
            activity_validation_rules={"validator": "code_runner", "language": "csharp"},
        )

        review = build_activity_concept_review(lesson)

        self.assertIsNotNone(review)
        self.assertEqual(review["title"], "Concept Review")
        self.assertIn("Conditional logic", review["summary"])

    def test_result_evaluator_concept_review_starts_hidden_and_shows_after_completion(self):
        render_course = Course.objects.create(
            title="C# Conditional UI Course",
            description="Render the gated concept review.",
            overview="Render only.",
        )
        Enrollment.objects.create(user=self.user, course=render_course)
        lesson = Lesson.objects.create(
            course=render_course,
            title="Conditional Statements",
            order=1,
            slug="csharp-conditional-statements",
            summary="Render the gated concept review.",
            lecture_content="<p>Lecture content.</p>",
            activity_title="Activity 3: Result Evaluator",
            activity_instructions="<p>Compile your code.</p>",
            activity_validation_rules={
                "validator": "code_runner",
                "language": "csharp",
                "starter_code": "using System;",
            },
        )

        response = self.client.get(reverse("lesson_detail", args=[render_course.slug, lesson.slug]))
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("data-runner-concept-review", content)
        self.assertRegex(content, r"data-runner-concept-review[^>]*hidden")

        progress = get_or_create_lesson_progress(self.user, lesson)
        progress.activity_completed = True
        progress.activity_status = progress.CORRECT
        progress.save()

        completed_response = self.client.get(reverse("lesson_detail", args=[render_course.slug, lesson.slug]))
        completed_content = completed_response.content.decode()

        self.assertEqual(completed_response.status_code, 200)
        self.assertIn("data-runner-concept-review", completed_content)
        self.assertNotRegex(completed_content, r"data-runner-concept-review[^>]*hidden")
        self.assertIn("Conditional logic helps a program choose between different outcomes.", completed_content)

    def test_python_code_runner_concept_review_starts_hidden_and_shows_after_completion(self):
        render_course = Course.objects.create(
            title="Python Runner UI Course",
            description="Render the shared concept review for code runner lessons.",
            overview="Render only.",
        )
        Enrollment.objects.create(user=self.user, course=render_course)
        lesson = Lesson.objects.create(
            course=render_course,
            title="Python Practice",
            order=1,
            slug="python-practice-ui",
            summary="Practice printing output clearly.",
            lecture_content="<p>Use print() to send output to the console.</p>",
            activity_title="Python Code Runner",
            activity_instructions="<p>Write a short Python program.</p>",
            activity_validation_rules={
                "validator": "code_runner",
                "language": "python",
                "starter_code": 'print("Hello")',
            },
        )

        response = self.client.get(reverse("lesson_detail", args=[render_course.slug, lesson.slug]))
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("data-runner-concept-review", content)
        self.assertRegex(content, r"data-runner-concept-review[^>]*hidden")

        progress = get_or_create_lesson_progress(self.user, lesson)
        progress.activity_completed = True
        progress.activity_status = progress.CORRECT
        progress.save()

        completed_response = self.client.get(reverse("lesson_detail", args=[render_course.slug, lesson.slug]))
        completed_content = completed_response.content.decode()

        self.assertEqual(completed_response.status_code, 200)
        self.assertIn("data-runner-concept-review", completed_content)
        self.assertNotRegex(completed_content, r"data-runner-concept-review[^>]*hidden")
        self.assertIn("Practice printing output clearly.", completed_content)

    def test_standard_activity_concept_review_starts_hidden_and_shows_after_completion(self):
        lesson = self.lesson_one

        response = self.client.get(reverse("lesson_detail", args=[self.course.slug, lesson.slug]))
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("data-runner-concept-review", content)
        self.assertRegex(content, r"data-runner-concept-review[^>]*hidden")

        progress = get_or_create_lesson_progress(self.user, lesson)
        progress.activity_completed = True
        progress.activity_status = progress.CORRECT
        progress.save()

        completed_response = self.client.get(reverse("lesson_detail", args=[self.course.slug, lesson.slug]))
        completed_content = completed_response.content.decode()

        self.assertEqual(completed_response.status_code, 200)
        self.assertIn("data-runner-concept-review", completed_content)
        self.assertNotRegex(completed_content, r"data-runner-concept-review[^>]*hidden")
        self.assertIn("Run deterministic Python code.", completed_content)

    def test_minimal_env_redirects_runner_profile_to_workspace(self):
        execution_root = Path(settings.BASE_DIR) / ".test_code_runner"
        execution_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=execution_root) as temp_dir:
            env = minimal_env(Path(temp_dir))

        self.assertTrue(env["HOME"].startswith(temp_dir))
        self.assertTrue(env["USERPROFILE"].startswith(temp_dir))
        self.assertTrue(env["APPDATA"].startswith(temp_dir))
        self.assertTrue(env["LOCALAPPDATA"].startswith(temp_dir))
        self.assertTrue(env["NUGET_PACKAGES"].startswith(temp_dir))

    def test_minimal_env_preserves_windows_dotnet_installation_paths(self):
        execution_root = Path(settings.BASE_DIR) / ".test_code_runner"
        execution_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=execution_root) as temp_dir:
            with patch.dict(
                os.environ,
                {
                    "ProgramFiles": r"C:\Program Files",
                    "ProgramFiles(x86)": r"C:\Program Files (x86)",
                    "CommonProgramFiles": r"C:\Program Files\Common Files",
                },
                clear=False,
            ):
                env = minimal_env(Path(temp_dir))

        self.assertEqual(env["ProgramFiles"], r"C:\Program Files")
        self.assertEqual(env["ProgramFiles(x86)"], r"C:\Program Files (x86)")
        self.assertEqual(env["CommonProgramFiles"], r"C:\Program Files\Common Files")
        self.assertEqual(env["DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE"], "true")
