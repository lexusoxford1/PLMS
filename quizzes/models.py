from django.conf import settings
from django.db import models


class Quiz(models.Model):
    lesson = models.OneToOneField("courses.Lesson", on_delete=models.CASCADE, related_name="quiz")
    title = models.CharField(max_length=200)
    instructions = models.TextField(blank=True)
    passing_score = models.PositiveIntegerField(default=70)
    max_attempts = models.PositiveIntegerField(
        default=0,
        help_text="Use 0 to allow unlimited attempts.",
    )
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["lesson__course", "lesson__order"]

    @property
    def total_points(self):
        return sum(question.points for question in self.questions.all())

    def __str__(self):
        return self.title


class Question(models.Model):
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_TEXT = "short_text"

    QUESTION_TYPE_CHOICES = (
        (MULTIPLE_CHOICE, "Multiple Choice"),
        (SHORT_TEXT, "Short Text"),
    )

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    prompt = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default=MULTIPLE_CHOICE)
    order = models.PositiveIntegerField(default=1)
    points = models.PositiveIntegerField(default=1)
    correct_text = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["quiz", "order"]

    @property
    def field_name(self):
        return f"question_{self.pk}"

    def is_correct_answer(self, submitted_value):
        if submitted_value in (None, ""):
            return False
        if self.question_type == self.SHORT_TEXT:
            return str(submitted_value).strip().casefold() == self.correct_text.strip().casefold()
        return self.choices.filter(pk=submitted_value, is_correct=True).exists()

    def __str__(self):
        return f"Question {self.order} for {self.quiz}"


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["question", "order"]

    def __str__(self):
        return self.text


class QuizAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    score = models.DecimalField(max_digits=5, decimal_places=2)
    passed = models.BooleanField(default=False)
    submitted_answers = models.JSONField(default=dict, blank=True)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-attempted_at"]

    def __str__(self):
        return f"{self.user} - {self.quiz} ({self.score}%)"
