"""Backward-compatible import for older configuration callers."""
from config.settings.email import SHOP_EMAIL_FROM_NAME, configure_email

configure_sendgrid_email = configure_email
