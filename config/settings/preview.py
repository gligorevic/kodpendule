"""Offline-safe local catalog preview. Deliberately never reads an env file.

Run with --settings=config.settings.preview; bind runserver to 127.0.0.1.
"""
from .base import *  # noqa: F403

DEBUG = True
SECRET_KEY = "local-preview-only-not-a-production-secret"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]", "testserver"]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000", "http://127.0.0.1:8000",
    "http://localhost:8001", "http://127.0.0.1:8001",
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}
DATABASE_ROUTERS = []
MEDIA_ROOT = BASE_DIR / "media"  # noqa: F405
MEDIA_URL = "/media/"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
USE_R2 = False
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
EMAIL_HOST = ""
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
SENDGRID_API_KEY = ""
DEFAULT_FROM_EMAIL = "preview@localhost"
SERVER_EMAIL = "preview@localhost"
SHOP_FROM_EMAIL = "preview@localhost"
SHOP_NOTIFICATION_EMAIL = "preview@localhost"
GOOGLE_MAPS_EMBED_URL = ""
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
LOCAL_CATALOG_PREVIEW = True
