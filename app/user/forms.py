from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

User = get_user_model()


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=200,
        required=True,
        help_text="Required.",
        label="First Name",
    )
    last_name = forms.CharField(
        max_length=200,
        required=True,
        help_text="Required.",
        label="Last Name",
    )
    email = forms.EmailField(
        max_length=200,
        required=True,
        help_text="Required. Enter a valid email address.",
        label="Email",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"autofocus": True}),
        max_length=200,
        required=True,
        help_text="Required.",
        label="Username",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
        required=True,
        help_text="Required.",
        label="Password",
    )
