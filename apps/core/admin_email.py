"""Read-only mail diagnostics; deliberately never exposes credentials."""
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.views.decorators.http import require_GET

from apps.core.mail import is_email_configured


@require_GET
def email_diagnostics(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    from django.contrib import admin
    backend = settings.EMAIL_BACKEND
    transport = "SendGrid HTTPS (443)" if backend == "apps.core.email_backends.SendGridAPIBackend" else "SMTP" if backend == "django.core.mail.backends.smtp.EmailBackend" else "Isključeno / lokalni režim"
    context = {
        **admin.site.each_context(request),
        "title": "Provera slanja mejlova",
        "configured": is_email_configured(),
        "transport": transport,
        "mail_host": getattr(settings, "EMAIL_HOST", "") if transport == "SMTP" else "",
        "mail_port": getattr(settings, "EMAIL_PORT", "") if transport == "SMTP" else "",
        "sender": settings.SHOP_FROM_EMAIL,
        "recipient": settings.SHOP_NOTIFICATION_EMAIL,
        "timeout": settings.EMAIL_TIMEOUT,
    }
    return TemplateResponse(request, "admin/email_diagnostics.html", context)
