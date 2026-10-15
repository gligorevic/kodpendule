from __future__ import annotations

import secrets
from decimal import Decimal

from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.accounts.services import archive_customer_from_checkout
from apps.cart.cart import Cart, CartLine
from apps.core.checkout_settings import checkout_today, resolve_checkout_shipping_price
from apps.orders.models import Order, OrderItem, OrderStatus, PaymentMethod
from apps.orders.payments.cod import CashOnDeliveryProvider
from apps.products.models import Product
from apps.products.services.stock_notifications import notify_low_stock_if_crossed_threshold
from apps.shipping.models import City


class CheckoutError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def generate_order_number() -> str:
    """Short customer-facing ID, e.g. KP-482917."""
    for _ in range(20):
        suffix = f"{secrets.randbelow(900_000) + 100_000:d}"
        candidate = f"KP-{suffix}"
        if not Order.objects.filter(order_number=candidate).exists():
            return candidate
    return f"KP-{secrets.randbelow(1_000_000):06d}"


@transaction.atomic
def create_order_from_checkout(
    *,
    cart: Cart,
    user,
    guest_email: str,
    first_name: str,
    last_name: str,
    phone: str,
    shipping_city: City,
    shipping_street: str,
    order_notes: str,
    payment_method: str,
    requested_delivery_date=None,
) -> Order:
    lines = cart.get_lines()
    if not lines:
        raise CheckoutError(_("Your cart is empty."))

    if payment_method not in PaymentMethod.values:
        raise CheckoutError(_("Please select how you want to pay."))

    _validate_stock(lines)

    delivery_date = requested_delivery_date or checkout_today()
    subtotal = cart.subtotal
    shipping_price = resolve_checkout_shipping_price(
        subtotal=subtotal,
        city=shipping_city,
        requested_delivery_date=delivery_date,
    )
    total = subtotal + shipping_price

    order = Order.objects.create(
        order_number=generate_order_number(),
        user=user if user and user.is_authenticated else None,
        guest_email=guest_email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        shipping_street=shipping_street,
        shipping_city_name=shipping_city.name,
        shipping_city=shipping_city,
        order_notes=order_notes,
        requested_delivery_date=delivery_date,
        shipping_price=shipping_price,
        payment_method=payment_method,
        status=OrderStatus.PENDING,
        subtotal=subtotal,
        total=total,
    )

    # Use the same lock order as inventory imports and other checkouts, even when
    # the customer's cart order differs. Retain that cart order for order items.
    locked_products = {
        product.pk: product
        for product in Product.objects.select_for_update()
        .filter(pk__in=[line.product.pk for line in lines], is_archived=False)
        .order_by("pk")
    }
    for line in lines:
        product = locked_products.get(line.product.pk)
        if product is None:
            raise CheckoutError(
                _("Not enough stock for %(name)s.")
                % {"name": line.product.safe_translation_getter("name", any_language=True) or line.product.sku}
            )
        if product.stock < line.quantity:
            raise CheckoutError(
                _("Not enough stock for %(name)s.")
                % {
                    "name": product.safe_translation_getter("name", any_language=True)
                    or product.sku
                }
            )
        stock_before = product.stock
        product.stock -= line.quantity
        product.save(update_fields=["stock"])

        notify_low_stock_if_crossed_threshold(
            product=product,
            stock_before=stock_before,
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.safe_translation_getter("name", any_language=True)
            or product.sku,
            sku=product.sku,
            unit_price=line.unit_price,
            quantity=line.quantity,
        )

    provider = CashOnDeliveryProvider()
    result = provider.charge(order)
    if not result.success:
        raise CheckoutError(result.message)

    archive_customer_from_checkout(
        email=guest_email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        delivery_street=shipping_street,
        delivery_city_name=shipping_city.name,
        user=user,
    )

    cart.clear()
    return order


def _validate_stock(lines: list[CartLine]) -> None:
    for line in lines:
        if line.quantity > line.product.stock:
            raise CheckoutError(
                _("Not enough stock for %(name)s.")
                % {
                    "name": line.product.safe_translation_getter("name", any_language=True)
                    or line.product.sku
                }
            )
