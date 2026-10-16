"""
Production — Render.com / Gunicorn + WhiteNoise + managed PostgreSQL.

Set env vars in the Render dashboard (see .env.production.example).
Optional: copy .env.production for local production smoke tests.
"""

from decouple import Csv

from config.settings.env import get_config

config = get_config(".env.production")

from .base import *  # noqa: E402, F403

DEBUG = config("DEBUG", default=False, cast=bool)
SECRET_KEY = config("SECRET_KEY")
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())

if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set in production.")

# --- Database (Render PostgreSQL — production only) ---------------------------

import dj_database_url  # noqa: E402

DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL"),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

if not DATABASES["default"]:
    raise ValueError("DATABASE_URL must be set in production.")

# --- WhiteNoise (static files) ------------------------------------------------

MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

WHITENOISE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

# --- Media (Cloudflare R2 when USE_R2=True) -----------------------------------

import sys  # noqa: E402

from config.settings.r2 import configure_r2  # noqa: E402

configure_r2(sys.modules[__name__], config)

# --- Security -----------------------------------------------------------------

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=False, cast=bool)

_csrf_origins = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())
if _csrf_origins:
    CSRF_TRUSTED_ORIGINS = _csrf_origins
else:
    CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if host]

# --- Email (HTTPS API or SMTP) ------------------------------------------------------

from config.settings.email import configure_email  # noqa: E402

configure_email(sys.modules[__name__], config)

GOOGLE_MAPS_EMBED_URL = config("GOOGLE_MAPS_EMBED_URL", default=GOOGLE_MAPS_EMBED_URL)  # noqa: F405

# --- Logging ------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": config("LOG_LEVEL", default="INFO"),
    },
    "loggers": {
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps.core.mail": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.orders.services.order_notifications": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.products.services.stock_notifications": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
