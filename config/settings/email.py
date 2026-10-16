"""Configurable transactional mail: HTTPS for SendGrid, or any SMTP provider."""
from django.core.exceptions import ImproperlyConfigured

SHOP_EMAIL_FROM_NAME = "Kod Pendule"


def configure_email(settings_module, config):
    sender = (config("SHOP_FROM_EMAIL", default="info@kodpendule.com") or "info@kodpendule.com").strip()
    settings_module.SHOP_FROM_EMAIL = sender
    settings_module.DEFAULT_FROM_EMAIL = sender
    settings_module.SERVER_EMAIL = sender
    settings_module.SHOP_NOTIFICATION_EMAIL = (config("SHOP_NOTIFICATION_EMAIL", default="kodpendule@gmail.com") or "kodpendule@gmail.com").strip()
    key = (config("SENDGRID_API_KEY", default="") or "").strip()
    host = (config("EMAIL_HOST", default="") or "").strip()
    provider = config("EMAIL_PROVIDER", default="auto").strip().lower()
    if provider == "auto":
        provider = "smtp" if host else "sendgrid" if key else "disabled"
    if provider not in {"smtp", "sendgrid", "disabled"}:
        raise ImproperlyConfigured("EMAIL_PROVIDER must be auto, smtp, sendgrid or disabled.")
    settings_module.EMAIL_PROVIDER = provider
    settings_module.SENDGRID_API_KEY = key
    settings_module.EMAIL_HOST = host
    settings_module.EMAIL_TIMEOUT = config("EMAIL_TIMEOUT", default=10, cast=int)
    settings_module.EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"
    if provider == "sendgrid":
        settings_module.EMAIL_BACKEND = "apps.core.email_backends.SendGridAPIBackend"
    elif provider == "smtp":
        settings_module.EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
        settings_module.EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
        settings_module.EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
        settings_module.EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
        settings_module.EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=False, cast=bool)
        settings_module.EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=not settings_module.EMAIL_USE_SSL, cast=bool)
        if settings_module.EMAIL_USE_SSL and settings_module.EMAIL_USE_TLS:
            raise ImproperlyConfigured("Use EMAIL_USE_TLS or EMAIL_USE_SSL, not both.")
