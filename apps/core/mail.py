"""SendGrid / SMTP email helpers for the shop."""

from __future__ import annotations

import logging
from email.utils import formataddr
from typing import Iterable

from django.conf import settings
from django.core.mail import EmailMessage

from config.settings.email import SHOP_EMAIL_FROM_NAME

logger = logging.getLogger(__name__)


def is_email_configured() -> bool:
    if settings.EMAIL_BACKEND == "django.core.mail.backends.dummy.EmailBackend":
        return False
    if settings.EMAIL_BACKEND == "apps.core.email_backends.SendGridAPIBackend":
        return bool(getattr(settings, "SENDGRID_API_KEY", ""))
    return bool(getattr(settings, "EMAIL_HOST", ""))


def shop_from_email() -> str:
    email = (
        getattr(settings, "SHOP_FROM_EMAIL", "")
        or settings.DEFAULT_FROM_EMAIL
    ).strip()
    return formataddr((SHOP_EMAIL_FROM_NAME, email))


def send_shop_email(
    *,
    subject: str,
    message: str,
    recipient_list: Iterable[str],
    reply_to: str | None = None,
    fail_silently: bool = True,
) -> bool:
    """
    Send a plain-text email. Returns True on success, False on skip/failure.

    Never raises when fail_silently=True (default).
    """
    recipients = [addr.strip() for addr in recipient_list if addr and addr.strip()]
    if not recipients:
        logger.warning("send_shop_email skipped: no recipients for subject %r", subject)
        return False

    if not is_email_configured():
        logger.warning(
            "send_shop_email skipped: email transport not configured (subject=%r, recipients=%s)",
            subject,
            recipients,
        )
        return False

    try:
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=shop_from_email(),
            to=recipients,
            reply_to=[reply_to] if reply_to else None,
        )
        accepted = email.send(fail_silently=False)
        if accepted != 1:
            logger.error("Email backend did not accept the message (recipient_count=%s)", len(recipients))
            return False
        logger.info("Email accepted by transport (recipient_count=%s)", len(recipients))
        return True
    except Exception:
        logger.exception(
            "Failed to send email: subject=%r to=%s",
            subject,
            recipients,
        )
        if not fail_silently:
            raise
        return False
