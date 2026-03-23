from django.core.management.base import BaseCommand

from courses.course_seed import COURSE_DEFINITIONS
from courses.models import Course, Lesson
from quizzes.models import Choice, Question, Quiz


def infer_course_category(course_data):
    title = (course_data.get("title") or "").lower()
    slug = (course_data.get("slug") or "").lower()
    if "c#" in title or "csharp" in slug:
        return Course.CATEGORY_CSHARP
    if "python" in title or "python" in slug:
        return Course.CATEGORY_PYTHON
    if "php" in title or "php" in slug:
        return Course.CATEGORY_PHP
    return Course.CATEGORY_GENERAL


class Command(BaseCommand):
    help = "Create or refresh the built-in C#, PHP, and Python programming courses."

    def handle(self, *args, **options):
        created_courses = 0
        updated_courses = 0

        for course_data in COURSE_DEFINITIONS:
            course, created = self.seed_course(course_data)
            if created:
                created_courses += 1
            else:
                updated_courses += 1
            self.stdout.write(self.style.SUCCESS(f"Prepared course: {course.title}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Programming course seed complete. Created {created_courses} course(s), updated {updated_courses} course(s)."
            )
        )

    def seed_course(self, course_data):
        course, created = Course.objects.update_or_create(
            slug=course_data["slug"],
            defaults={
                "title": course_data["title"],
                "description": course_data["description"],
                "category": infer_course_category(course_data),
                "overview": course_data["overview"],
                "difficulty": course_data["difficulty"],
                "estimated_hours": course_data["estimated_hours"],
                "is_published": True,
            },
        )

        kept_lesson_ids = []
        for order, lesson_data in enumerate(course_data["lessons"], start=1):
            lesson, _ = Lesson.objects.update_or_create(
                course=course,
                order=order,
                defaults={
                    "title": lesson_data["title"],
                    "slug": lesson_data["slug"],
                    "summary": lesson_data["summary"],
                    "lecture_content": lesson_data["lecture_content"],
                    "activity_title": lesson_data["activity_title"],
                    "activity_instructions": lesson_data["activity_instructions"],
                    "activity_hint": lesson_data["activity_hint"],
                    "activity_validation_rules": lesson_data.get("activity_validation", {}),
                    "is_published": True,
                },
            )
            kept_lesson_ids.append(lesson.id)

            if lesson_data.get("quiz"):
                self.seed_quiz(lesson, lesson_data["quiz"])
            else:
                Quiz.objects.filter(lesson=lesson).delete()

        course.lessons.exclude(id__in=kept_lesson_ids).delete()
        return course, created

    def seed_quiz(self, lesson, quiz_data):
        quiz, _ = Quiz.objects.update_or_create(
            lesson=lesson,
            defaults={
                "title": quiz_data["title"],
                "instructions": quiz_data["instructions"],
                "passing_score": quiz_data["passing_score"],
                "max_attempts": 0,
                "is_published": True,
            },
        )
        quiz.questions.all().delete()

        for order, question_data in enumerate(quiz_data["questions"], start=1):
            question = Question.objects.create(
                quiz=quiz,
                prompt=question_data["prompt"],
                question_type=Question.MULTIPLE_CHOICE,
                order=order,
                points=1,
            )
            for choice_order, choice_text in enumerate(question_data["choices"], start=1):
                Choice.objects.create(
                    question=question,
                    text=choice_text,
                    is_correct=(choice_order - 1) == question_data["correct_index"],
                    order=choice_order,
                )
