"""
Local development — venv + SQLite.

  set DJANGO_SETTINGS_MODULE=config.settings.local
  copy .env.local.example → .env.local

Production on Render uses PostgreSQL (config.settings.production).
Keep queries ORM-only so both databases behave the same.
"""

import sys
from pathlib import Path

from decouple import Csv

from config.settings.env import get_config

config = get_config(".env.local")

from .base import *  # noqa: E402, F403

DEBUG = config("DEBUG", default=True, cast=bool)
SECRET_KEY = config("SECRET_KEY", default="dev-only-insecure-change-me")
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# --- Database (SQLite) ----------------------------------------------------------

_db_name = "test_db.sqlite3" if "test" in sys.argv else "db.sqlite3"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / _db_name,  # noqa: F405
    }
}

# --- Dev tools ----------------------------------------------------------------

INTERNAL_IPS = ["127.0.0.1", "localhost"]

# Django admin changelist breaks on Python 3.14 (template Context.__copy__).
# Use Python 3.12 for local dev, or set USE_DEBUG_TOOLBAR=True on 3.12 only.
_use_toolbar = config("USE_DEBUG_TOOLBAR", default=False, cast=bool)
if DEBUG and _use_toolbar and sys.version_info < (3, 14):
    try:
        import debug_toolbar  # noqa: F401

        INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
        MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
    except ImportError:
        pass

# --- Security (relaxed for local HTTP) ----------------------------------------

CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="http://localhost:8000,http://127.0.0.1:8000",
    cast=Csv(),
)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# --- Media (optional Cloudflare R2 via .env.local) ----------------------------

import sys  # noqa: E402

from config.settings.r2 import configure_r2  # noqa: E402

configure_r2(sys.modules[__name__], config)

# --- Email (optional HTTPS API or SMTP) ------------------------------

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
        "django.db.backends": {
            "handlers": ["console"],
            "level": config("DB_LOG_LEVEL", default="WARNING"),
            "propagate": False,
        },
    },
}
