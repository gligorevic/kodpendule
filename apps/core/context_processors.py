from django.conf import settings

from apps.cart.cart import get_cart
from apps.categories.selectors import get_nav_categories
from apps.core.contact_details import resolve_contact_details
from apps.core.cookie_consent import consent_given
from apps.core.models import FooterSettings, SiteSettings
from apps.core.utils import get_shop_language
from apps.products.selectors import promo_products_qs, recommended_products_qs


def shop_globals(request):
    if request.path.startswith("/admin"):
        maps_url = (getattr(settings, "GOOGLE_MAPS_EMBED_URL", "") or "").strip()
        return {
            "site_settings": None,
            "footer_settings": None,
            "footer_contact": resolve_contact_details(None),
            "nav_categories": [],
            "shop_currency_symbol": settings.SHOP_CURRENCY_SYMBOL,
            "shop_language": "sr",
            "cart_item_count": 0,
            "google_maps_embed_url": maps_url,
            "cookie_consent_given": True,
            "cookie_consent_cookie_name": settings.COOKIE_CONSENT_COOKIE_NAME,
            "cookie_consent_version": settings.COOKIE_CONSENT_VERSION,
            "cookie_consent_max_age": settings.COOKIE_CONSENT_MAX_AGE,
        }

    language = get_shop_language(request)
    site = SiteSettings.objects.language(language).filter(pk=1).first()
    footer = FooterSettings.objects.language(language).filter(pk=1).first()
    cart = get_cart(request)
    maps_url = (getattr(settings, "GOOGLE_MAPS_EMBED_URL", "") or "").strip()

    return {
        "site_settings": site,
        "footer_settings": footer,
        "footer_contact": resolve_contact_details(footer),
        "nav_categories": get_nav_categories(language),
        "shop_currency_symbol": settings.SHOP_CURRENCY_SYMBOL,
        "shop_language": language,
        "cart_item_count": cart.total_items,
        "has_promo_products": promo_products_qs(language).exists(),
        "has_recommended_products": recommended_products_qs(language).exists(),
        "google_maps_embed_url": maps_url,
        "cookie_consent_given": consent_given(request),
        "cookie_consent_cookie_name": settings.COOKIE_CONSENT_COOKIE_NAME,
        "cookie_consent_version": settings.COOKIE_CONSENT_VERSION,
        "cookie_consent_max_age": settings.COOKIE_CONSENT_MAX_AGE,
    }
