"""Combinable product filters for store managers."""
from django.contrib import admin
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _
from apps.categories.models import Category

class StockFilter(admin.SimpleListFilter):
    title = _("Stock")
    template = "admin/includes/filter_select.html"
    parameter_name = "stock_state"
    def lookups(self, request, model_admin):
        return (("out", _("Out of stock")), ("low", _("Low stock alerts")), ("available", _("In stock")))
    def queryset(self, request, queryset):
        if self.value() == "out": return queryset.filter(stock=0)
        if self.value() == "low": return queryset.filter(stock__lte=F("minimum_stock_alert"))
        if self.value() == "available": return queryset.filter(stock__gt=0)
        return queryset

class PhotoFilter(admin.SimpleListFilter):
    title = _("Product image")
    template = "admin/includes/filter_select.html"
    parameter_name = "photo"
    def lookups(self, request, model_admin):
        return (("missing", _("Without photo")), ("present", _("With photo")))
    def queryset(self, request, queryset):
        missing = Q(main_image="") | Q(main_image__isnull=True)
        if self.value() == "missing": return queryset.filter(missing)
        if self.value() == "present": return queryset.exclude(missing)
        return queryset

class ProductCategoryFilter(admin.SimpleListFilter):
    title = _("Category")
    parameter_name = "category"
    template = "admin/includes/filter_select.html"
    def lookups(self, request, model_admin):
        categories = Category.objects.select_related("parent").prefetch_related("translations", "parent__translations").order_by("sort_order", "pk")
        return [(str(c.pk), f"{c.parent} / {c}" if c.parent_id else str(c)) for c in categories]
    def queryset(self, request, queryset):
        value = self.value()
        if value is None: return queryset
        if not value.isdigit(): return queryset.none()
        ids = {int(value)}
        pairs = list(Category.objects.values_list("pk", "parent_id"))
        while True:
            children = {pk for pk, parent in pairs if parent in ids} - ids
            if not children: break
            ids.update(children)
        return queryset.filter(category_id__in=ids)
