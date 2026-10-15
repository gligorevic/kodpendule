"""Read-only order queries for storefront tracking and history."""

from django.db.models import QuerySet

from apps.orders.models import Order


def order_detail_qs() -> QuerySet[Order]:
    return (
        Order.objects.select_related(
            "user",
            "shipping_city",
        ).prefetch_related("items", "items__product", "items__product__translations")
    )


def normalize_order_number(order_number: str) -> str:
    number = (order_number or "").strip().upper().replace(" ", "")
    if number.isascii() and number.isdigit():
        number = f"KP-{number}"
    return number


def get_order_for_guest_tracking(
    order_number: str,
) -> dict | None:
    """Return public progress only. A number never grants access to personal details."""
    number = normalize_order_number(order_number)
    if not number:
        return None
    return (
        Order.objects.filter(order_number__iexact=number)
        .values("order_number", "status", "requested_delivery_date")
        .first()
    )


def get_order_for_user(user, order_number: str) -> Order | None:
    if not user or not getattr(user, "is_authenticated", False) or not user.is_authenticated:
        return None
    number = normalize_order_number(order_number)
    if not number:
        return None
    return (
        order_detail_qs()
        .filter(user_id=user.pk, order_number__iexact=number)
        .first()
    )


def orders_for_user(user) -> QuerySet[Order]:
    if not user or not user.is_authenticated:
        return Order.objects.none()
    return (
        order_detail_qs()
        .filter(user_id=user.pk)
        .order_by("-created_at")
    )
