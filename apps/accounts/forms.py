from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import CustomerProfile, User
from apps.accounts.services import archive_customer_from_registration
from apps.accounts.services.customer_archive import normalize_customer_email
from apps.core.form_errors import apply_latin_required_messages


class LoginForm(AuthenticationForm):
    """Sign in with username and password."""

    username = forms.CharField(
        label=_("Username"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "username",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "current-password",
            }
        ),
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        apply_latin_required_messages(self)


class RegistrationForm(UserCreationForm):
    """Create account with profile fields."""

    email = forms.EmailField(
        label=_("Email"),
        required=True,
        help_text=_("Required for order confirmations."),
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "autocomplete": "email",
            },
        ),
    )
    first_name = forms.CharField(
        label=_("First name"),
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "autocomplete": "given-name"},
        ),
    )
    last_name = forms.CharField(
        label=_("Last name"),
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "autocomplete": "family-name"},
        ),
    )
    phone = forms.CharField(
        label=_("Phone"),
        required=True,
        max_length=32,
        widget=forms.TextInput(
            attrs={"class": "form-control", "autocomplete": "tel"},
        ),
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control", "autocomplete": "username"},
            ),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        apply_latin_required_messages(self)
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "autocomplete": "new-password"},
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "autocomplete": "new-password"},
        )

    def clean_email(self) -> str:
        email = normalize_customer_email(self.cleaned_data.get("email", ""))
        if not email:
            raise forms.ValidationError(_("Email is required."))
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("A user with that email already exists."))
        return email

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        if commit:
            user.save()
            CustomerProfile.objects.create(
                user=user,
                phone=self.cleaned_data.get("phone", ""),
            )
            archive_customer_from_registration(user)
        return user


class CustomerContactImportForm(forms.Form):
    csv_file = forms.FileField(
        label=_("CSV file"),
        help_text=_("UTF-8 CSV with a header row. Required column: email."),
    )
