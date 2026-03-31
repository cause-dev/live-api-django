from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import LoginForm

urlpatterns = [
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="user/login.html", authentication_form=LoginForm
        ),
        name="login",
    ),
    path("logout", views.logout_view, name="logout"),
]
