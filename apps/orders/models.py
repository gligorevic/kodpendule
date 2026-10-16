from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.fields import MoneyField


class OrderStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    CONFIRMED = "confirmed", _("Confirmed")
    PROCESSING = "processing", _("Processing")
    SHIPPED = "shipped", _("Shipped")
    DELIVERED = "delivered", _("Delivered")
    CANCELLED = "cancelled", _("Cancelled")


class PaymentMethod(models.TextChoices):
    CARD = "card", _("Pay by card")
    CASH = "cash", _("Pay in cash")


class Order(models.Model):
    order_number = models.CharField(
        _("Order number"),
        max_length=32,
        unique=True,
        db_index=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("User"),
    )
    guest_email = models.EmailField(
        _("Guest email"),
        help_text=_("Used for guest orders and order tracking."),
    )

    first_name = models.CharField(_("First name"), max_length=120)
    last_name = models.CharField(_("Last name"), max_length=120)
    phone = models.CharField(_("Phone"), max_length=32)

    shipping_street = models.CharField(_("Shipping street"), max_length=255)
    shipping_city_name = models.CharField(
        _("Shipping city name"),
        max_length=120,
        help_text=_("City name as entered by customer."),
    )
    shipping_city = models.ForeignKey(
        "shipping.City",
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name=_("Shipping city"),
    )

    order_notes = models.TextField(
        _("Order notes"),
        blank=True,
        help_text=_("Optional note from checkout."),
    )
    age_confirmed_at = models.DateTimeField(
        _("18+ confirmation time"), null=True, blank=True, editable=False,
    )
    requested_delivery_date = models.DateField(
        _("Requested delivery date"),
        help_text=_("Customer's preferred delivery date from checkout."),
    )
    shipping_price = MoneyField(verbose_name=_("Shipping price"), default=0)

    payment_method = models.CharField(
        _("Payment method"),
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
    )
    is_new = models.BooleanField(
        _("New (unread)"),
        default=True,
        db_index=True,
        help_text=_("Marked as read when opened in admin."),
    )

    subtotal = MoneyField(verbose_name=_("Subtotal"), default=0)
    total = MoneyField(verbose_name=_("Total"), default=0)

    created_at = models.DateTimeField(_("Created at"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        verbose_name = _("order")
        verbose_name_plural = _("orders")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["guest_email"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self) -> str:
        return self.order_number

    @property
    def is_guest_order(self) -> bool:
        return self.user_id is None

    @property
    def customer_email(self) -> str:
        """Email for this order (checkout field; may differ from account email)."""
        if self.guest_email:
            return self.guest_email
        if self.user_id and self.user.email:
            return self.user.email
        return ""

    @property
    def customer_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def delivery_address_display(self) -> str:
        street = (self.shipping_street or "").strip()
        city = (self.shipping_city_name or "").strip()
        if street and city:
            return f"{street}, {city}"
        return street or city


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Order"),
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name=_("Product"),
    )
    product_name = models.CharField(_("Product name"), max_length=255)
    sku = models.CharField(_("SKU"), max_length=64)
    unit_price = MoneyField(
        verbose_name=_("Unit price"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    quantity = models.PositiveIntegerField(
        _("Quantity"),
        validators=[MinValueValidator(1)],
    )

    class Meta:
        verbose_name = _("order item")
        verbose_name_plural = _("order items")
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["product"]),
        ]

    def __str__(self) -> str:
        return f"{self.sku} x {self.quantity}"

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity
