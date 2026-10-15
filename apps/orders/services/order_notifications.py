from __future__ import annotations

import logging

from django.utils.translation import gettext as _

from apps.core.email_recipients import shop_admin_recipients, shop_reply_to_email
from apps.core.mail import send_shop_email
from apps.orders.models import Order
from apps.orders.services.order_email_body import build_order_details_text

logger = logging.getLogger(__name__)


def notify_customer_new_order(order: Order) -> None:
    """Send order confirmation to the customer."""
    email = (order.customer_email or "").strip()
    if not email:
        logger.warning(
            "Customer order email skipped: no email on order %s",
            order.order_number,
        )
        return

    subject = _("Your order %(number)s. Kod Pendule") % {"number": order.order_number}
    intro = _(
        "Thank you for your order! We have received it and will contact you "
        "if we need any additional information."
    )
    body = "\n\n".join([intro, build_order_details_text(order)])

    send_shop_email(
        subject=subject,
        message=body,
        recipient_list=[email],
        reply_to=shop_reply_to_email(),
    )


def notify_staff_new_order(order: Order) -> None:
    """Notify shop staff about a new order."""
    recipients = shop_admin_recipients()
    if not recipients:
        logger.warning(
            "Staff order notification skipped: no recipients (order %s)",
            order.order_number,
        )
        return

    subject = _("New order %(number)s") % {"number": order.order_number}
    intro = _("A new order has been placed on the shop.")
    body = "\n\n".join([intro, build_order_details_text(order)])

    send_shop_email(
        subject=subject,
        message=body,
        recipient_list=recipients,
    )
