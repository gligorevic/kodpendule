from django.conf import settings
from django.http import Http404
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

from apps.categories.selectors import get_category_by_slug
from apps.core.breadcrumbs import (
    category_breadcrumb_items,
    home_crumb,
    products_crumb,
)
from apps.core.mixins import ShopLanguageMixin
from apps.core.utils import activate_parler_language
from apps.core.templatetags.shop_tags import product_meta_title
from apps.products.models import Product
from apps.products.selectors import (
    active_products_qs,
    apply_catalog_filters,
    filter_products_by_category,
    get_product_by_slug,
    promo_products_qs,
    recommended_products_qs,
    related_products,
)


class CatalogControlsMixin:
    """GET controls shared by the catalog and scoped category/promo listings."""

    sort_options = (
        ("default", _("Default order")),
        ("price_asc", _("Price: low to high")),
        ("price_desc", _("Price: high to low")),
        ("newest", _("Newest first")),
    )

    @cached_property
    def catalog_filters(self):
        sort = self.request.GET.get("sort", "default")
        return {
            "query": self.request.GET.get("q", "").strip()[:200],
            "available_only": self.request.GET.get("available") == "1",
            "sort": sort if sort in dict(self.sort_options) else "default",
        }

    def filter_catalog(self, queryset):
        return apply_catalog_filters(
            queryset, language=self.shop_language, **self.catalog_filters
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for product in context.get("products", []):
            activate_parler_language(product, self.shop_language)
        filters = self.catalog_filters
        context.update({
            "search_query": filters["query"],
            "available_only": filters["available_only"],
            "catalog_sort": filters["sort"],
            "catalog_sort_options": self.sort_options,
            "has_catalog_filters": bool(filters["query"] or filters["available_only"] or filters["sort"] != "default"),
            "catalog_form_action": self.request.path,
        })
        return context


class ProductListView(CatalogControlsMixin, ShopLanguageMixin, ListView):
    template_name = "products/list.html"
    context_object_name = "products"
    paginate_by = settings.SHOP_PRODUCTS_PER_PAGE

    def get_queryset(self):
        qs = active_products_qs(self.shop_language)
        category_slug = self.request.GET.get("kategorija", "").strip()
        self.active_category = None
        if category_slug:
            self.active_category = get_category_by_slug(category_slug, self.shop_language)
            if self.active_category:
                qs = filter_products_by_category(
                    self.active_category,
                    self.shop_language,
                    include_children=True,
                    queryset=qs,
                )
        return self.filter_catalog(qs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.catalog_filters["query"]
        active_category = self.active_category
        root = active_category
        while root and root.parent_id:
            root = root.parent

        if query:
            meta_title = _("Search results for “%(query)s”") % {"query": query}
        elif active_category:
            meta_title = active_category.name
        else:
            meta_title = _("Products")

        breadcrumbs = [home_crumb(), products_crumb()]
        if active_category:
            activate_parler_language(active_category, self.shop_language)
            breadcrumbs = category_breadcrumb_items(
                active_category, self.shop_language
            )
        elif query:
            breadcrumbs = [home_crumb(), products_crumb(), (_("Search"), None)]

        context.update(
            {
                "search_query": query,
                "active_category": active_category,
                "active_category_root_id": root.pk if root else None,
                "catalog_has_categories": True,
                "breadcrumb_items": breadcrumbs,
                "meta_title": meta_title,
                "meta_description": _("Browse our product catalog."),
                "canonical_url": self.request.build_absolute_uri(
                    self.request.path
                ),
            }
        )
        return context


class PromoProductListView(CatalogControlsMixin, ShopLanguageMixin, ListView):
    template_name = "products/list.html"
    context_object_name = "products"
    paginate_by = settings.SHOP_PRODUCTS_PER_PAGE

    def get_queryset(self):
        return self.filter_catalog(promo_products_qs(self.shop_language))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for product in context.get("products", []):
            activate_parler_language(product, self.shop_language)
        context.update(
            {
                "catalog_title": _("Promo sales"),
                "catalog_subtitle": _(
                    "Browse products with a reduced price."
                ),
                "breadcrumb_items": [
                    home_crumb(),
                    products_crumb(),
                    (_("Promo sales"), None),
                ],
                "meta_title": _("Promo sales"),
                "meta_description": _("Browse products on promo sale."),
                "canonical_url": self.request.build_absolute_uri(self.request.path),
                "hide_category_nav": True,
            }
        )
        return context


class RecommendedProductListView(CatalogControlsMixin, ShopLanguageMixin, ListView):
    template_name = "products/list.html"
    context_object_name = "products"
    paginate_by = settings.SHOP_PRODUCTS_PER_PAGE

    def get_queryset(self):
        return self.filter_catalog(recommended_products_qs(self.shop_language))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for product in context.get("products", []):
            activate_parler_language(product, self.shop_language)
        context.update(
            {
                "catalog_title": _("Recommended products"),
                "catalog_subtitle": _(
                    "Explore our selected products."
                ),
                "breadcrumb_items": [
                    home_crumb(),
                    products_crumb(),
                    (_("Recommended products"), None),
                ],
                "meta_title": _("Recommended products"),
                "meta_description": _("Browse our recommended products."),
                "canonical_url": self.request.build_absolute_uri(self.request.path),
                "hide_category_nav": True,
            }
        )
        return context


class ProductDetailView(ShopLanguageMixin, DetailView):
    template_name = "products/detail.html"
    context_object_name = "product"

    def get_object(self, queryset=None):
        product = get_product_by_slug(self.kwargs["slug"], self.shop_language)
        if product is None:
            raise Http404(_("Product not found."))
        return product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product: Product = self.object
        gallery = list(product.gallery_images.all())
        context["gallery_images"] = gallery
        context["gallery_image_count"] = len(gallery) + bool(product.main_image)
        context["product_short_description"] = (product.safe_translation_getter("short_description", "") or "").strip()
        context["product_description"] = (product.safe_translation_getter("description", "") or "").strip()
        context["related_products"] = related_products(product, self.shop_language)
        activate_parler_language(product.category, self.shop_language)
        context["breadcrumb_items"] = category_breadcrumb_items(
            product.category,
            self.shop_language,
            link_current_category=True,
        )
        context["breadcrumb_items"].append((product.name, None))
        context["meta_title"] = product_meta_title(
            product, context.get("site_settings")
        )
        context["meta_description"] = (
            product.safe_translation_getter("meta_description")
            or product.safe_translation_getter("short_description", "")
        )
        context["canonical_url"] = self.request.build_absolute_uri()
        return context
