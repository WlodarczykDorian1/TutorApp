import json
from typing import Any, Dict

from courses.choices import GradeChoices, SchoolLevelChoices
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, TemplateView, View
from plans.models import UserPlan
from plans.services import PlanService

from .forms import LoginForm, UserRegisterForm
from .models import User
from .services import UserService


class UserRegisterView(CreateView):
    model = User
    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")

    def form_valid(self, form: UserRegisterForm) -> HttpResponse:
        service = UserService()
        service.register_user(form)
        messages.success(
            self.request, _("Account has been created. You can now log in.")
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["grade_choices_json"] = json.dumps(
            {
                SchoolLevelChoices.PRIMARY: [
                    [choice[0], str(choice[1])]
                    for choice in GradeChoices.choices
                    if choice[0] in UserService.PRIMARY_GRADES
                ],
                SchoolLevelChoices.SECONDARY: [
                    [choice[0], str(choice[1])]
                    for choice in GradeChoices.choices
                    if choice[0] in UserService.SECONDARY_GRADES
                ],
            }
        )
        return context

    def form_invalid(self, form: UserRegisterForm) -> HttpResponse:
        messages.error(
            self.request,
            "There was an error creating your account. Please correct the form below.",
        )
        return super().form_invalid(form)


class LoginView(View):
    template_name: str = "users/login.html"
    form_class = LoginForm
    success_url = reverse_lazy("users:home")

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return render(request, self.template_name, {"form": self.form_class()})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            service = UserService()
            user = service.login_user(request, username, password)

            if user:
                user_plan = UserPlan.objects.filter(user=user).first()
                if user_plan:
                    PlanService(user_plan).downgrade_if_expired()

                messages.success(request, _("You have been successfully logged in."))
                return redirect(self.success_url)

            messages.error(request, _("Invalid username or password."))
        return render(request, self.template_name, {"form": form})


class LogoutView(View):
    """Log the current user out and redirect to the login page.

    Only POST is accepted to protect against CSRF-based logout.
    """

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        service = UserService(user=request.user)
        service.logout_user(request)
        return redirect("users:login")


class HomeView(LoginRequiredMixin, TemplateView):
    template_name: str = "users/home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Home")
        return context


class CustomPasswordResetView(PasswordResetView):
    template_name: str = "users/password_reset_form.html"
    email_template_name: str = "users/password_reset_email.html"
    subject_template_name: str = "users/password_reset_subject.txt"
    success_url = reverse_lazy("users:password_reset_done")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Reset your password")
        return context


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name: str = "users/password_reset_done.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Check your email")
        return context


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name: str = "users/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Set your new password")
        return context


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name: str = "users/password_reset_complete.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = _("Password reset complete")
        return context
