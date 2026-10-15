from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView

from apps.categories.models import Category
from apps.categories.selectors import (
    category_path_for_url,
    get_category_by_path,
    get_category_by_slug,
    get_child_categories,
    get_nav_categories,
)
from apps.core.storefront_urls import shop_reverse
from apps.core.breadcrumbs import category_breadcrumb_items, home_crumb
from apps.core.mixins import ShopLanguageMixin
from apps.core.utils import activate_parler_language
from apps.core.templatetags.shop_tags import category_meta_title
from apps.products.selectors import filter_products_by_category
from apps.products.views import CatalogControlsMixin


class CategoryListView(ShopLanguageMixin, ListView):
    template_name = "categories/list.html"

    def get_queryset(self):
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        root_categories = list(get_nav_categories(self.shop_language))
        for category in root_categories:
            activate_parler_language(category, self.shop_language)
        context.update(
            {
                "root_categories": root_categories,
                "breadcrumb_items": [home_crumb(), (_("Categories"), None)],
                "meta_title": _("Categories"),
                "meta_description": _("Browse product categories."),
                "canonical_url": self.request.build_absolute_uri(),
            }
        )
        return context


class CategoryDetailView(CatalogControlsMixin, ShopLanguageMixin, ListView):
    template_name = "categories/detail.html"
    context_object_name = "products"
    paginate_by = settings.SHOP_PRODUCTS_PER_PAGE

    def dispatch(self, request, *args, **kwargs):
        path = (kwargs.get("category_path") or "").strip("/")
        self.category = get_category_by_path(path, self.shop_language)
        if self.category is None and path and "/" not in path:
            legacy = get_category_by_slug(path, self.shop_language)
            if legacy is not None:
                canonical = legacy.get_absolute_url()
                if canonical != request.path:
                    return redirect(canonical, permanent=True)
        if self.category is None:
            raise Http404(_("Category not found."))
        canonical_path = category_path_for_url(self.category, self.shop_language)
        if canonical_path and path != canonical_path:
            return redirect(
                shop_reverse(
                    "categories:detail",
                    category_path=canonical_path,
                ),
                permanent=True,
            )
        self.child_categories = list(
            get_child_categories(self.category, self.shop_language)
        )
        for child in self.child_categories:
            activate_parler_language(child, self.shop_language)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.filter_catalog(filter_products_by_category(
            self.category,
            self.shop_language,
            include_children=True,
        ))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.category
        for product in context.get("products", []):
            activate_parler_language(product, self.shop_language)
        context.update(
            {
                "category": category,
                "child_categories": self.child_categories,
                "show_child_categories": bool(self.child_categories),
                "category_description": (category.safe_translation_getter("description", "") or "").strip(),
                "breadcrumb_items": category_breadcrumb_items(
                    category, self.shop_language
                ),
                "meta_title": category_meta_title(
                    category, context.get("site_settings")
                ),
                "meta_description": (
                    category.safe_translation_getter("meta_description")
                    or (category.safe_translation_getter("description") or "")[:160]
                ),
                "canonical_url": self.request.build_absolute_uri(),
            }
        )
        return context
