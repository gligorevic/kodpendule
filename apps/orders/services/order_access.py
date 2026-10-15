"""Session-based access for guest order detail pages (after checkout)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.http import HttpRequest

    from apps.orders.models import Order

SESSION_KEY = "order_access_ids"
MAX_TRACKED_IDS = 10


def grant_order_access(request: HttpRequest, order: Order) -> None:
    """Remember that this browser may view the given order detail page."""
    ids: list[int] = list(request.session.get(SESSION_KEY, []))
    if order.pk not in ids:
        ids.append(order.pk)
    request.session[SESSION_KEY] = ids[-MAX_TRACKED_IDS:]
    request.session.modified = True


def user_can_view_order(request: HttpRequest, order: Order) -> bool:
    user = request.user
    if user.is_authenticated and order.user_id == user.pk:
        return True
    return order.pk in request.session.get(SESSION_KEY, [])
