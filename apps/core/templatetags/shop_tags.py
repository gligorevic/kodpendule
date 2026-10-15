from decimal import Decimal
import re

from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def pagination_pages(page):
    return page.paginator.get_elided_page_range(page.number, on_each_side=1, on_ends=1)


@register.filter
def plain_copy(value) -> str:
    """Keep legacy CMS copy consistent with storefront punctuation."""
    return re.sub(r"\s*—\s*(\w)", lambda match: ". " + match[1].upper(), str(value or "")).replace("—", "")


@register.filter
def money(value) -> str:
    """Format a decimal price with currency symbol (RSD)."""
    if value is None:
        return ""
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    formatted = f"{value:,.2f}".replace(",", " ").replace(".", ",")
    return f"{formatted} {settings.SHOP_CURRENCY_SYMBOL}"


@register.simple_tag
def product_meta_title(product, site_settings=None) -> str:
    title = product.safe_translation_getter("meta_title") or product.name
    if site_settings:
        site_name = site_settings.safe_translation_getter("site_name") or ""
        if site_name:
            return f"{title} | {site_name}"
    return title


@register.simple_tag
def category_meta_title(category, site_settings=None) -> str:
    title = category.safe_translation_getter("meta_title") or category.name
    if site_settings:
        site_name = site_settings.safe_translation_getter("site_name") or ""
        if site_name:
            return f"{title} | {site_name}"
    return title
