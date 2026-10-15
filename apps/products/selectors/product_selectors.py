from django.db.models import Count, F, Q, QuerySet

from apps.categories.models import Category
from apps.core.slugs import translation_languages_to_try
from apps.core.utils import get_shop_language
from apps.products.models import Product


def _language(language: str | None) -> str:
    return language or get_shop_language()


def active_products_qs(language: str | None = None) -> QuerySet[Product]:
    """Products visible on the storefront (active + at least one non-empty slug)."""
    _language(language)
    slug_filter = Q(
        translations__slug__isnull=False,
    ) & ~Q(translations__slug="")
    return (
        Product.objects.filter(is_archived=False)
        .annotate(slug_count=Count("translations", filter=slug_filter))
        .filter(slug_count__gt=0)
        .select_related("category")
        .prefetch_related("translations", "category__translations", "gallery_images")
        .order_by("-created_at")
    )


def get_product_by_slug(slug: str, language: str | None = None) -> Product | None:
    lang = _language(language)
    base_qs = (
        Product.objects.filter(is_archived=False)
        .select_related("category")
        .prefetch_related("translations", "category__translations", "gallery_images")
    )
    for try_lang in translation_languages_to_try(lang):
        product = base_qs.filter(
            translations__language_code=try_lang,
            translations__slug=slug,
        ).distinct().first()
        if product is not None:
            product.set_current_language(lang)
            return product
    product = base_qs.filter(translations__slug=slug).distinct().first()
    if product is not None:
        product.set_current_language(lang)
    return product


def filter_products_by_category(
    category: Category,
    language: str | None = None,
    *,
    include_children: bool = False,
) -> QuerySet[Product]:
    qs = active_products_qs(language)
    if include_children:
        category_ids = _collect_category_ids(category, language)
        return qs.filter(category_id__in=category_ids)
    return qs.filter(category=category)


def _collect_category_ids(category: Category, language: str | None) -> list[int]:
    ids = [category.pk]
    children = (
        Category.objects.filter(is_active=True, parent=category)
        .values_list("pk", flat=True)
    )
    for child_id in children:
        child = Category.objects.filter(pk=child_id).first()
        if child:
            ids.extend(_collect_category_ids(child, language))
    return ids


def search_products(query: str, language: str | None = None) -> QuerySet[Product]:
    q = query.strip()
    if not q:
        return active_products_qs(language).none()
    lang = _language(language)
    return active_products_qs(lang).filter(
        Q(sku__icontains=q)
        | Q(translations__language_code=lang, translations__name__icontains=q)
        | Q(
            translations__language_code=lang,
            translations__short_description__icontains=q,
        )
    ).distinct()


def recommended_products_qs(language: str | None = None) -> QuerySet[Product]:
    return (
        active_products_qs(language)
        .filter(is_recommended=True)
        .order_by("recommended_order", "-updated_at")
    )


def promo_products_qs(language: str | None = None) -> QuerySet[Product]:
    """Products with an active discount (promo price lower than regular price)."""
    return (
        active_products_qs(language)
        .filter(
            discount_price__isnull=False,
            discount_price__lt=F("price"),
        )
        .order_by("-updated_at")
    )


def related_products(product: Product, language: str | None = None, limit: int = 4) -> QuerySet[Product]:
    return (
        active_products_qs(language)
        .filter(category=product.category)
        .exclude(pk=product.pk)[:limit]
    )
