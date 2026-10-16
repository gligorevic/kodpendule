from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.categories.models import Category
from apps.core.kp_admin import KPTranslatableAdmin
from apps.core.slugs import localized_slug, unique_slug_for_translation


@admin.register(Category)
class CategoryAdmin(KPTranslatableAdmin):
    translatable_fields = (
        "name",
        "slug",
        "description",
        "meta_title",
        "meta_description",
    )
    list_display = ("image_preview", "name", "parent", "product_count", "is_active", "sort_order")
    list_display_links = ("name",)
    list_filter = ("is_active", ("parent", admin.EmptyFieldListFilter))
    search_help_text = _("Search categories by name.")
    search_fields = ("translations__name", "translations__slug")
    list_select_related = ("parent",)
    fieldsets = (
        (_("Category structure"), {"fields": ("name", "parent", "is_active", "sort_order", "requires_age_confirmation")}),
        (_("Category image"), {"fields": ("image",)}),
        (_("Descriptions"), {"classes": ("collapse",), "fields": ("description",)}),
        (_("SEO"), {"classes": ("collapse",), "fields": ("slug", "meta_title", "meta_description")}),
    )

    @admin.display(description=_("Category image"))
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img class="kp-product-thumb" src="{}" alt="" loading="lazy" width="48" height="48">', obj.image.url)
        return "—"

    @admin.display(description=_("Products"))
    def product_count(self, obj):
        return obj.product_total

    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj, **kwargs)

        def autofill_slug_for_translation(trans, master):
            return unique_slug_for_translation(trans)

        form_class.autofill_slug_for_translation = autofill_slug_for_translation
        return form_class

    @admin.display(description=_("Slug"))
    def slug_display(self, obj: Category) -> str:
        return localized_slug(obj) or "—"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("parent")
            .annotate(product_total=Count("products", distinct=True))
            .prefetch_related("translations", "parent__translations")
        )
