from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.checkout_settings import DeliveryTiming, checkout_today, min_scheduled_delivery_date
from apps.core.form_errors import apply_latin_required_messages
from apps.orders.models import PaymentMethod
from apps.shipping.selectors import active_cities


class CheckoutForm(forms.Form):
    guest_email = forms.EmailField(
        label=_("Email"),
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
    )
    first_name = forms.CharField(
        label=_("First name"),
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "given-name"}),
    )
    last_name = forms.CharField(
        label=_("Last name"),
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "family-name"}),
    )
    phone = forms.CharField(
        label=_("Phone"),
        max_length=32,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "tel", "type": "tel", "inputmode": "tel"}),
    )

    shipping_city = forms.ModelChoiceField(
        label=_("City"),
        queryset=active_cities(),
        empty_label=_("Select city"),
        widget=forms.Select(attrs={"class": "form-select", "id": "id_shipping_city", "autocomplete": "address-level2"}),
    )
    shipping_street = forms.CharField(
        label=_("Street and number"),
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "street-address"}),
    )

    delivery_timing = forms.ChoiceField(
        label=_("When should we deliver?"),
        choices=DeliveryTiming.choices,
        initial=DeliveryTiming.SAME_DAY,
        widget=forms.RadioSelect(attrs={"class": "shop-delivery-timing__input"}),
    )
    requested_delivery_date = forms.DateField(
        label=_("Preferred delivery date"),
        required=False,
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
                "id": "id_requested_delivery_date",
            }
        ),
        help_text=_("Choose any date after today. Delivery is free for scheduled orders."),
    )

    order_notes = forms.CharField(
        label=_("Order note"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": _("Delivery instructions, building entrance, etc. (optional)"),
            }
        ),
    )

    payment_method = forms.ChoiceField(
        label=_("Payment method"),
        choices=PaymentMethod.choices,
        widget=forms.RadioSelect(attrs={"class": "shop-payment-method__input"}),
        error_messages={
            "required": _("Please select how you want to pay."),
        },
    )

    accept_legal = forms.BooleanField(
        required=True,
        label=_("I have read and accept the Terms of Service and Privacy Policy."),
        error_messages={
            "required": _(
                "You must accept the Terms of Service and Privacy Policy to place an order."
            ),
        },
        widget=forms.CheckboxInput(
            attrs={
                "class": "shop-checkout-legal__checkbox",
            }
        ),
    )

    def __init__(self, *args, user=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        apply_latin_required_messages(self)
        self.user = user
        self.show_email_field = True

        if user and user.is_authenticated:
            self.fields["guest_email"].widget.attrs["autocomplete"] = "off"

        min_date = min_scheduled_delivery_date()
        self.fields["requested_delivery_date"].widget.attrs["min"] = min_date.isoformat()

    def full_clean(self):
        super().full_clean()
        for name, field in self.fields.items():
            # Radio/consent errors remain in their existing shared components.
            if name in {"delivery_timing", "payment_method", "accept_legal"}:
                continue
            described_by = []
            if field.help_text:
                described_by.append(f"{self[name].auto_id}_helptext")
            if name in self.errors:
                field.widget.attrs["aria-invalid"] = "true"
                described_by.append(f"{self[name].auto_id}_errors")
            if described_by:
                field.widget.attrs["aria-describedby"] = " ".join(described_by)

    def clean(self):
        cleaned = super().clean()
        timing = cleaned.get("delivery_timing")
        today = checkout_today()

        if timing == DeliveryTiming.SAME_DAY:
            cleaned["requested_delivery_date"] = today
        elif timing == DeliveryTiming.SCHEDULED:
            delivery_date = cleaned.get("requested_delivery_date")
            if not delivery_date:
                self.add_error(
                    "requested_delivery_date",
                    _("Choose a delivery date."),
                )
            elif delivery_date <= today:
                self.add_error(
                    "requested_delivery_date",
                    _("Choose a date after today for free scheduled delivery."),
                )
        return cleaned

    def clean_guest_email(self) -> str:
        email = (self.cleaned_data.get("guest_email") or "").strip()
        if not email:
            raise forms.ValidationError(_("Email is required for checkout."))
        return email

    def clean_order_notes(self) -> str:
        return (self.cleaned_data.get("order_notes") or "").strip()
