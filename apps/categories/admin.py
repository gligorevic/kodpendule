from django.contrib import admin
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
    list_display = ("name", "slug_display", "parent", "is_active", "sort_order")
    search_fields = ("translations__name", "translations__slug")
    list_select_related = ("parent",)
    fieldsets = (
        (
            _("Name & URL"),
            {
                "fields": ("name", "slug", "description"),
            },
        ),
        (None, {"fields": ("parent", "image", "is_active", "sort_order", "requires_age_confirmation")}),
    )

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
            .prefetch_related("translations", "parent__translations")
        )
