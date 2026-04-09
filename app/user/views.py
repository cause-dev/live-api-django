from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.views import (
    LoginView as DjangoLoginView,
    LogoutView as DjangoLogoutView,
)
from django.views.generic import CreateView

from config.template_registry import T
from .forms import SignUpForm, LoginForm

# Create your views here.


class RegisterView(CreateView):
    form_class = SignUpForm
    template_name = "user/register.html"
    success_url = reverse_lazy("login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["base_template"] = (
            T["LAYOUT"]["HTMX_BASE"] if self.request.htmx else T["LAYOUT"]["BASE"]
        )
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get("username")
        messages.success(
            self.request, f"Account created for {username}! You can now log in."
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class LoginView(DjangoLoginView):
    template_name = "user/login.html"
    authentication_form = LoginForm
    success_url = reverse_lazy("dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["base_template"] = (
            T["LAYOUT"]["HTMX_BASE"] if self.request.htmx else T["LAYOUT"]["BASE"]
        )
        return context

    def form_valid(self, form):
        messages.success(self.request, "You have successfully logged in.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)


class LogoutView(DjangoLogoutView):
    next_page = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "You have been logged out.")
        return super().dispatch(request, *args, **kwargs)
