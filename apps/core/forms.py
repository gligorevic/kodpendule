from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.form_errors import apply_latin_required_messages


class ContactForm(forms.Form):
    name = forms.CharField(
        label=_("Your name"),
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "name"}),
    )
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
    )
    phone = forms.CharField(
        label=_("Phone (optional)"),
        max_length=32,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "tel"}),
    )
    message = forms.CharField(
        label=_("Message"),
        min_length=10,
        max_length=4000,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": _("How can we help you?"),
            }
        ),
    )
    # Honeypot — hidden from users; bots often fill it.
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "tabindex": "-1",
                "autocomplete": "off",
                "aria-hidden": "true",
            }
        ),
    )

    def clean_website(self) -> str:
        return (self.cleaned_data.get("website") or "").strip()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        apply_latin_required_messages(self)

    def is_spam_submission(self) -> bool:
        return bool(self.cleaned_data.get("website"))
