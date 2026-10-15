from django import forms
from django.utils.translation import gettext_lazy as _

from apps.orders.selectors.order_selectors import normalize_order_number


class GuestOrderTrackForm(forms.Form):
    order_number = forms.CharField(
        label=_("Order number"),
        max_length=32,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("example: KP-123456"),
                "autocomplete": "off",
                "autocapitalize": "characters",
                "spellcheck": "false",
                "aria-describedby": "order-number-help",
            }
        ),
    )

    def clean_order_number(self) -> str:
        return normalize_order_number(self.cleaned_data["order_number"])
