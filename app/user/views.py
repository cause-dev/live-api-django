from django.http import HttpResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import (
    LoginView as DjangoLoginView,
    LogoutView as DjangoLogoutView,
)
from django.views.generic import CreateView

from .forms import SignUpForm, LoginForm

# Create your views here.


class RegisterView(CreateView):
    form_class = SignUpForm
    template_name = "user/register.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get("username")
        messages.success(
            self.request, f"Account created for {username}! You can now log in."
        )

        if self.request.htmx:
            response = HttpResponse()
            response["HX-Redirect"] = self.get_success_url()
            return response
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        if self.request.htmx:
            return self.render_to_response(self.get_context_data(form=form))
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "url_name": "register",
                "btn_label": "Create Account",
                "is_register": True,
            }
        )
        return context


class LoginView(DjangoLoginView):
    template_name = "user/login.html"
    authentication_form = LoginForm
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        login(self.request, form.get_user())
        messages.success(self.request, "Welcome back! You have successfully logged in.")

        if self.request.htmx:
            response = HttpResponse()
            response["HX-Redirect"] = self.get_success_url()
            return response

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password. Please try again.")
        if self.request.htmx:
            return self.render_to_response(self.get_context_data(form=form))
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "url_name": "login",
                "btn_label": "Login",
                "is_register": False,
            }
        )
        return context


class LogoutView(DjangoLogoutView):
    next_page = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        messages.success(request, "You have been logged out.")
        if request.htmx:
            response = HttpResponse()
            response["HX-Redirect"] = self.next_page
            return response
        return response
