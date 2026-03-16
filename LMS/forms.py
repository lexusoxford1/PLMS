from django import forms


class ActivitySubmissionForm(forms.Form):
    response = forms.CharField(
        label="Activity response",
        widget=forms.Textarea(attrs={"rows": 6}),
        help_text="Provide your answer, code snippet, or explanation for this lesson activity.",
    )


class LectureCompletionForm(forms.Form):
    confirm = forms.BooleanField(
        initial=True,
        required=True,
        label="I have completed this lecture",
    )
