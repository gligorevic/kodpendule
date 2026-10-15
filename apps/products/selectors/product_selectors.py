from django.db.models import Case, Count, F, Q, QuerySet, Value, When
from django.db.models.functions import Lower, Replace

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
    queryset: QuerySet[Product] | None = None,
) -> QuerySet[Product]:
    qs = active_products_qs(language) if queryset is None else queryset
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


def search_products(
    query: str,
    language: str | None = None,
    *,
    queryset: QuerySet[Product] | None = None,
) -> QuerySet[Product]:
    q = query.strip()[:200]
    qs = active_products_qs(language) if queryset is None else queryset
    if not q:
        return qs.none()
    lang = _language(language)
    # Normalize before LOWER: SQLite's LOWER only handles ASCII, unlike PostgreSQL.
    # SQL expressions keep pagination and category filters in the database.
    replacements = {"č": "c", "ć": "c", "š": "s", "ž": "z", "đ": "dj"}
    replacements.update({key.upper(): value for key, value in list(replacements.items())})

    def folded(field):
        expression = F(field)
        for source, target in replacements.items():
            expression = Replace(expression, Value(source), Value(target))
        return Lower(expression)

    terms = list(dict.fromkeys(q.translate(str.maketrans(replacements)).lower().split()))[:8]
    qs = qs.alias(
        search_name=folded("translations__name"),
        search_description=folded("translations__short_description"),
        search_sku=folded("sku"),
    )
    match = Q()
    for term in terms:
        match &= (
            Q(search_sku__contains=term) | Q(barcode__icontains=term)
            | (Q(translations__language_code__in=translation_languages_to_try(lang))
               & (Q(search_name__contains=term) | Q(search_description__contains=term)))
        )
    return qs.filter(match).distinct()


def apply_catalog_filters(
    queryset: QuerySet[Product],
    *,
    query: str = "",
    available_only: bool = False,
    sort: str = "default",
    language: str | None = None,
) -> QuerySet[Product]:
    """Refine an existing catalog scope without replacing category/promo filters."""
    qs = queryset
    if query:
        qs = search_products(query, language, queryset=qs)
    if available_only:
        qs = qs.filter(stock__gt=0)
    if sort in {"price_asc", "price_desc"}:
        qs = qs.annotate(
            catalog_price=Case(
                When(discount_price__lt=F("price"), then=F("discount_price")),
                default=F("price"),
            )
        )
        return qs.order_by("catalog_price" if sort == "price_asc" else "-catalog_price", "pk")
    if sort == "newest":
        return qs.order_by("-created_at", "-pk")
    # The final key keeps pagination deterministic when timestamps/orders tie.
    return qs.order_by(*qs.query.order_by, "pk")


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
