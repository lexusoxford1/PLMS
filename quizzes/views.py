from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from LMS.permissions import learner_required
from LMS.utils import can_access_lesson, get_or_create_lesson_progress
from certificates.models import Certificate

from .forms import QuizSubmissionForm
from .models import Question, Quiz, QuizAttempt


def grade_quiz(quiz, cleaned_data):
    total_points = 0
    earned_points = 0
    submitted_answers = {}

    for question in quiz.questions.prefetch_related("choices").all():
        total_points += question.points
        answer = cleaned_data.get(question.field_name)
        submitted_answers[str(question.pk)] = answer
        if question.question_type == Question.MULTIPLE_CHOICE and answer not in (None, ""):
            answer = int(answer)
        if question.is_correct_answer(answer):
            earned_points += question.points

    score = round((earned_points / total_points) * 100, 2) if total_points else 0
    return score, score >= quiz.passing_score, submitted_answers


@learner_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(
        Quiz.objects.select_related("lesson", "lesson__course"),
        pk=quiz_id,
        is_published=True,
    )
    lesson = quiz.lesson
    course = lesson.course

    if not can_access_lesson(request.user, lesson):
        messages.warning(request, "This quiz is locked until the lesson becomes available.")
        return redirect("course_detail", slug=course.slug)

    progress = get_or_create_lesson_progress(request.user, lesson)
    if not progress.lecture_completed or (lesson.has_activity and not progress.activity_completed):
        messages.warning(request, "Complete the lecture and activity before taking the quiz.")
        return redirect("lesson_detail", course_slug=course.slug, lesson_slug=lesson.slug)

    attempt_count = quiz.attempts.filter(user=request.user).count()
    if quiz.max_attempts and attempt_count >= quiz.max_attempts and not progress.quiz_passed:
        messages.error(request, "You have reached the maximum number of quiz attempts for this lesson.")
        return redirect("lesson_detail", course_slug=course.slug, lesson_slug=lesson.slug)

    if request.method == "POST":
        form = QuizSubmissionForm(quiz, request.POST)
        if form.is_valid():
            score, passed, submitted_answers = grade_quiz(quiz, form.cleaned_data)
            QuizAttempt.objects.create(
                user=request.user,
                quiz=quiz,
                score=Decimal(str(score)),
                passed=passed,
                submitted_answers=submitted_answers,
            )
            if passed:
                certificate = Certificate.objects.filter(user=request.user, course=course).first()
                if certificate:
                    messages.success(request, f"Quiz passed with {score}%. Course completed and certificate unlocked.")
                    return redirect("certificate_detail", pk=certificate.pk)
                messages.success(
                    request,
                    f"Quiz passed with {score}%. The next lesson is now unlocked when available, and your XP progress has been updated.",
                )
            else:
                messages.error(request, f"Quiz not passed. Your score is {score}%. Please review and try again.")
            return redirect("lesson_detail", course_slug=course.slug, lesson_slug=lesson.slug)
    else:
        form = QuizSubmissionForm(quiz)

    attempts = quiz.attempts.filter(user=request.user)
    return render(
        request,
        "quizzes/quiz_page.html",
        {
            "quiz": quiz,
            "lesson": lesson,
            "course": course,
            "form": form,
            "attempts": attempts,
            "progress": progress,
        },
    )
