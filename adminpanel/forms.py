from django import forms
from django.contrib.auth import get_user_model
from django.utils.html import strip_tags

from badges.models import Badge
from courses.models import Course, LearningMaterial, Lesson


User = get_user_model()


class AdminLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput())


class CourseAdminForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            "title",
            "description",
            "category",
            "overview",
            "difficulty",
            "estimated_hours",
            "image",
            "is_published",
        ]

    def clean_title(self):
        value = (self.cleaned_data.get("title") or "").strip()
        if not value:
            raise forms.ValidationError("Course title is required.")
        return value


class LessonAdminForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            "course",
            "title",
            "order",
            "summary",
            "image",
            "lecture_content",
            "is_published",
        ]

    def clean_title(self):
        value = (self.cleaned_data.get("title") or "").strip()
        if not value:
            raise forms.ValidationError("Lecture title is required.")
        return value

    def clean_lecture_content(self):
        value = self.cleaned_data.get("lecture_content") or ""
        if not strip_tags(value).strip():
            raise forms.ValidationError("Lecture content cannot be empty.")
        return value


class LearningMaterialAdminForm(forms.ModelForm):
    class Meta:
        model = LearningMaterial
        fields = [
            "lesson",
            "title",
            "order",
            "description",
            "material_type",
            "source_type",
            "presentation_provider",
            "external_url",
            "file",
        ]

    def clean_title(self):
        value = (self.cleaned_data.get("title") or "").strip()
        if not value:
            raise forms.ValidationError("Material title is required.")
        return value

    def clean_external_url(self):
        return (self.cleaned_data.get("external_url") or "").strip()


class BadgeAdminForm(forms.ModelForm):
    class Meta:
        model = Badge
        fields = [
            "name",
            "description",
            "icon",
            "course",
            "award_type",
            "criteria_key",
            "xp_reward",
            "is_active",
        ]

    def clean_name(self):
        value = (self.cleaned_data.get("name") or "").strip()
        if not value:
            raise forms.ValidationError("Badge name is required.")
        return value

    def clean_xp_reward(self):
        value = self.cleaned_data.get("xp_reward")
        if value is None or value < 0:
            raise forms.ValidationError("XP reward must be zero or greater.")
        return value


class UserRoleAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "role", "is_active"]

    def clean_email(self):
        return (self.cleaned_data.get("email") or "").strip()
