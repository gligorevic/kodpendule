"""
Shared Django settings for Kod Pendule webshop.

Do not put secrets here. Use config.settings.local or config.settings.production.

Database: local = SQLite, production = PostgreSQL. Use portable ORM only
(no postgres-only fields, indexes, or raw SQL).
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# --- Apps ---------------------------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "parler",
    "django_extensions",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.categories",
    "apps.products",
    "apps.cart",
    "apps.checkout",
    "apps.orders",
    "apps.shipping",
    "apps.dashboard",
    # Tombstone app: migrations only (newsletter feature removed).
    "apps.newsletter",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# --- Core ---------------------------------------------------------------------

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    # After LocaleMiddleware: default storefront to sr (ignore Accept-Language until /jezik/).
    "apps.core.middleware.StorefrontDefaultSerbianMiddleware",
    "apps.core.middleware.AdminSerbianLocaleMiddleware",
    "apps.core.middleware.StorefrontLocalizedUrlMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "apps.core.context_processors.shop_globals",
            ],
        },
    },
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# --- i18n ---------------------------------------------------------------------
# Default project language (admin + fallback). Storefront uses sr for new visitors;
# English only after the user picks it via /jezik/ (django_language cookie).
# AdminSerbianLocaleMiddleware forces sr on /admin/*.

LANGUAGE_CODE = "sr"
LANGUAGES = [
    ("sr", "Srpski"),
    ("en", "Engleski"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
FORMAT_MODULE_PATH = ["config.formats"]
TIME_ZONE = "Europe/Belgrade"
USE_I18N = True
USE_L10N = True
USE_TZ = True
DATE_FORMAT = "d/m/Y"
SHORT_DATE_FORMAT = "d/m/Y"
DATETIME_FORMAT = "d/m/Y H:i"
SHORT_DATETIME_FORMAT = "d/m/Y H:i"

PARLER_DEFAULT_LANGUAGE_CODE = "sr"
PARLER_LANGUAGES = {
    None: (
        {"code": "sr"},
        {"code": "en"},
    ),
    "default": {
        "fallbacks": ["sr"],
        "hide_untranslated": False,
    },
}

# --- Static & media (URLs; storage backends set per environment) --------------

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Cloudflare R2 (enabled in production/local via configure_r2)
USE_R2 = False

# --- Session & auth redirects (views wired in Step 4) -------------------------

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 2 weeks
LOGIN_URL = "/prijava/"
LOGIN_REDIRECT_URL = "/nalog/narudzbine/"
LOGOUT_REDIRECT_URL = "/"

# --- Shop ---------------------------------------------------------------------

SHOP_CURRENCY = "RSD"
SHOP_CURRENCY_SYMBOL = "din"
SHOP_PRODUCTS_PER_PAGE = 12

# All shop alerts (orders, low stock, contact form) are delivered to this inbox.
SHOP_NOTIFICATION_EMAIL = "kodpendule@gmail.com"

# Outgoing From address (must be authorized by your mail provider).
SHOP_FROM_EMAIL = "info@kodpendule.com"

# Configure SENDGRID_API_KEY for HTTPS, or EMAIL_HOST for SMTP.
EMAIL_HOST = ""
EMAIL_PROVIDER = "disabled"
EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"
EMAIL_TIMEOUT = 10
SENDGRID_API_KEY = ""
DEFAULT_FROM_EMAIL = SHOP_FROM_EMAIL
SERVER_EMAIL = SHOP_FROM_EMAIL

# Google Maps embed — Karađorđeva 11, Vrdnik (override via GOOGLE_MAPS_EMBED_URL in env)
# Cookie consent banner (storefront)
COOKIE_CONSENT_COOKIE_NAME = "kp_cookie_consent"
COOKIE_CONSENT_VERSION = "v1"
COOKIE_CONSENT_MAX_AGE = 60 * 60 * 24 * 365  # 1 year

GOOGLE_MAPS_EMBED_URL = (
    "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2814.666880361573!"
    "2d19.78775037612322!3d45.13308577107046!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!"
    "4f13.1!3m3!1m2!1s0x475b0625ce3ee8d9%3A0x6d1e2f1c22a7e5d1!2zS2FyYcSRb3LEkWV2YSAxMSwgVnJkbmlr!"
    "5e0!3m2!1sen!2srs!4v1780344704504!5m2!1sen!2srs"
)

