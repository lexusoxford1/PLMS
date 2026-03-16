from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import UserProfileForm, UserRegistrationForm


class ProviderAwareLoginView(LoginView):
    template_name = "auth/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["social_providers"] = settings.SOCIAL_LOGIN_PROVIDERS
        return context


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = "auth/register.html"
    success_url = reverse_lazy("dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["social_providers"] = settings.SOCIAL_LOGIN_PROVIDERS
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Your PLMS account is ready. Welcome aboard.")
        return response


@login_required
def profile_view(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("profile")
    else:
        form = UserProfileForm(instance=request.user)

    return render(
        request,
        "auth/profile.html",
        {
            "form": form,
            "social_providers": settings.SOCIAL_LOGIN_PROVIDERS,
        },
    )
