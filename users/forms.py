import re

from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.forms import UserCreationForm

from .models import User


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].strip().lower()
        user.role = User.LEARNER
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = (
            "profile_picture",
            "first_name",
            "last_name",
            "title",
            "organization",
            "email",
            "phone_number",
            "certificate_name",
            "bio",
        )
        widgets = {
            "profile_picture": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "first_name": forms.TextInput(attrs={"placeholder": "First name"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Last name"}),
            "title": forms.TextInput(attrs={"placeholder": "Learner title or current role"}),
            "organization": forms.TextInput(attrs={"placeholder": "School, company, or team"}),
            "email": forms.EmailInput(attrs={"placeholder": "name@example.com"}),
            "phone_number": forms.TextInput(attrs={"placeholder": "+63 912 345 6789"}),
            "certificate_name": forms.TextInput(
                attrs={"placeholder": "Optional display name for certificates"}
            ),
            "bio": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Share your learning goals, focus areas, or a short professional summary.",
                }
            ),
        }
        help_texts = {
            "certificate_name": "Leave blank to use your full name on certificates.",
            "organization": "Optional profile detail that can appear on certificates.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["profile_picture"].label = "Profile picture"
        self.fields["title"].label = "Role or title"
        self.fields["organization"].label = "Organization"
        self.fields["phone_number"].label = "Phone number"
        self.fields["certificate_name"].label = "Certificate display name"
        self.fields["bio"].label = "Bio / description"

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        duplicate = User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists()
        if duplicate:
            raise forms.ValidationError("This email address is already used by another learner.")
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number", "").strip()
        if phone_number and not re.fullmatch(r"[0-9()+\-\s]{7,40}", phone_number):
            raise forms.ValidationError("Enter a valid phone number using digits, spaces, or + - ( ).")
        return phone_number


class ProfilePasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "old_password": "Current password",
            "new_password1": "New password",
            "new_password2": "Confirm new password",
        }
        for name, placeholder in placeholders.items():
            self.fields[name].widget.attrs.update({"placeholder": placeholder})
