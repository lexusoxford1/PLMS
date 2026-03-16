from django import forms

from .models import Question


class QuizSubmissionForm(forms.Form):
    def __init__(self, quiz, *args, **kwargs):
        self.quiz = quiz
        super().__init__(*args, **kwargs)
        for question in quiz.questions.prefetch_related("choices").all():
            if question.question_type == Question.SHORT_TEXT:
                self.fields[question.field_name] = forms.CharField(
                    label=question.prompt,
                    required=True,
                    widget=forms.TextInput(),
                )
            else:
                self.fields[question.field_name] = forms.ChoiceField(
                    label=question.prompt,
                    required=True,
                    choices=[(choice.pk, choice.text) for choice in question.choices.all()],
                    widget=forms.RadioSelect,
                )

    def iter_fields(self):
        for question in self.quiz.questions.all():
            yield question, self[question.field_name]
