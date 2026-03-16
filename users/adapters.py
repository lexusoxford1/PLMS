from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.utils.text import slugify

from .models import User


def _unique_username(seed):
    base = slugify(seed)[:150] or "learner"
    candidate = base
    counter = 2
    while User.objects.filter(username=candidate).exists():
        suffix = f"-{counter}"
        candidate = f"{base[: max(1, 150 - len(suffix))]}{suffix}"
        counter += 1
    return candidate


class PLMSSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        email = (data.get("email") or "").strip().lower()
        if email:
            user.email = email

        if not user.username:
            username_seed = (
                data.get("username")
                or email.split("@")[0]
                or data.get("name")
                or data.get("first_name")
                or "learner"
            )
            user.username = _unique_username(username_seed)

        user.auth_provider = sociallogin.account.provider
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)
        update_fields = []

        if getattr(user, "auth_provider", "") != sociallogin.account.provider:
            user.auth_provider = sociallogin.account.provider
            update_fields.append("auth_provider")

        if user.email:
            normalized_email = user.email.strip().lower()
            if normalized_email != user.email:
                user.email = normalized_email
                update_fields.append("email")

        if update_fields:
            user.save(update_fields=update_fields)

        return user
