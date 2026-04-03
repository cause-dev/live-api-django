from django import forms
from .models import Monitor


class AddAPIForm(forms.ModelForm):
    class Meta:
        model = Monitor
        fields = ["name", "url", "expected_status_code", "is_active"]

        # Add DaisyUI classes to make the form look good
        widgets = {
            "name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "url": forms.URLInput(attrs={"class": "input input-bordered w-full"}),
            "expected_status_code": forms.NumberInput(
                attrs={"class": "input input-bordered w-full"}
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "toggle toggle-primary"}),
        }
