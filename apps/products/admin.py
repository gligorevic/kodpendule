from decimal import Decimal, ROUND_HALF_UP

from django import forms
from django.contrib import admin, messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from apps.products.admin_filters import StockFilter, PhotoFilter, ProductCategoryFilter
from django.utils.translation import gettext_lazy as _
from apps.core.admin_display import price_cell, slug_warning_cell, stock_cell
from apps.core.kp_admin import KPTranslatableAdmin
from apps.core.slugs import localized_slug, unique_slug_for_translation
from apps.products.models import Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    verbose_name = _("Gallery image")
    verbose_name_plural = _("Gallery images")
    fields = ("image", "alt_text_sr", "alt_text_en", "sort_order")
    classes = ("kp-inline-gallery",)

    def get_extra(self, request, obj=None, **kwargs):
        return 0 if obj is None else 1


class PromoSaleForm(forms.Form):
    discount_percent = forms.DecimalField(
        label=_("Discount percent"),
        min_value=Decimal("0.01"),
        max_value=Decimal("95"),
        decimal_places=2,
        required=False,
        help_text=_("Example: 15 means 15% discount from regular price."),
    )


_PRODUCT_FIELDSETS = (
    (_("Product details"), {"fields": ("name", "category", "sku", "barcode")}),
    (_("Pricing & stock"), {"fields": ("price", "discount_price", "stock", "minimum_stock_alert", "is_archived")}),
    (_("Product image"), {"fields": ("main_image",)}),
    (_("Descriptions"), {"classes": ("collapse",), "fields": ("short_description", "description")}),
    (_("Image source"), {"classes": ("collapse",), "fields": ("main_image_source_url", "main_image_attribution", "main_image_license_url")}),
    (_("SEO"), {"classes": ("collapse",), "description": _("Optional — used by search engines."), "fields": ("slug", "meta_title", "meta_description")}),
)

@admin.register(Product)
class ProductAdmin(KPTranslatableAdmin):
    translatable_fields = (
        "name",
        "slug",
        "short_description",
        "description",
        "meta_title",
        "meta_description",
    )
    change_list_template = "admin/products/product/change_list.html"
    change_form_template = "admin/products/product/change_form.html"
    list_display = (
        "photo_preview",
        "sku",
        "name",
        "category",
        "price_display",
        "stock_display",
    )
    search_fields = ("sku", "barcode", "translations__name", "translations__slug")
    list_select_related = ("category",)
    list_filter = (ProductCategoryFilter, StockFilter, PhotoFilter, "is_archived")
    list_display_links = ("sku", "name")
    search_help_text = _("Search by product name, SKU or barcode.")
    inlines = [ProductImageInline]
    list_per_page = 25
    save_on_top = True

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(_PRODUCT_FIELDSETS)
        if obj is not None:
            fieldsets.append(
                (
                    _("Timestamps"),
                    {
                        "fields": ("created_at", "updated_at"),
                        "classes": ("collapse",),
                    },
                ),
            )
        from apps.core.admin_translatable import expand_fieldsets

        return expand_fieldsets(fieldsets, self.translatable_fields)

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return ("created_at", "updated_at")
        return ()

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if not formfield:
            return formfield
        help_map = {
            "sku": _(
                "Internal code (e.g. S1). Not the product title on the shop — use Name above."
            ),
            "stock": _("Units available to sell."),
            "minimum_stock_alert": _(
                "Show a low-stock warning at or below this quantity."
            ),
        }
        if db_field.name in help_map:
            formfield.help_text = help_map[db_field.name]
        return formfield

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("category")
            .prefetch_related("translations", "category__translations")
        )

    def save_formset(self, request, form, formset, change):
        if formset.model is not ProductImage:
            super().save_formset(request, form, formset, change)
            return

        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.image:
                continue
            instance.save()
        for deleted in formset.deleted_objects:
            deleted.delete()

        product = form.instance
        if not product.pk or not product.main_image:
            return
        main_name = product.main_image.name
        duplicates = product.gallery_images.exclude(image="").filter(image=main_name)
        if duplicates.exists():
            duplicates.delete()

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "import-image/",
                self.admin_site.admin_view(self.catalog_image_upload_view),
                name="products_product_import_image",
            ),
            path(
                "import-xml/",
                self.admin_site.admin_view(self.inventory_import_view),
                name="products_product_import_xml",
            ),
            path(
                "import-xml/<uuid:batch_id>/",
                self.admin_site.admin_view(self.inventory_import_view),
                name="products_product_xml_preview",
            ),
            path(
                "promo-sales/",
                self.admin_site.admin_view(self.promo_sales_view),
                name="products_product_promo_sales",
            ),
            path(
                "recommended/",
                self.admin_site.admin_view(self.recommended_products_view),
                name="products_product_recommended",
            ),
        ]
        return custom_urls + urls

    def catalog_image_upload_view(self, request):
        from apps.products.catalog_image_upload import catalog_image_upload

        return catalog_image_upload(request, self)

    def inventory_import_view(self, request, batch_id=None):
        from apps.products.inventory_admin import inventory_import_view

        return inventory_import_view(self, request, batch_id=batch_id)

    def _product_admin_queryset(self, request):
        return (
            Product.objects.all()
            .select_related("category")
            .prefetch_related("translations", "category__translations")
            .order_by("-updated_at")
        )

    def recommended_products_view(self, request: HttpRequest) -> HttpResponse:
        if not self.has_change_permission(request):
            return redirect("admin:index")

        product_qs = self._product_admin_queryset(request)
        if request.method == "POST":
            selected_ids = request.POST.getlist("recommended")
            try:
                selected_pks = [int(pk) for pk in selected_ids]
            except ValueError:
                selected_pks = []

            Product.objects.update(is_recommended=False, recommended_order=0)
            if selected_pks:
                products_by_pk = {
                    p.pk: p for p in product_qs.filter(pk__in=selected_pks)
                }
                for order, pk in enumerate(selected_pks):
                    product = products_by_pk.get(pk)
                    if not product:
                        continue
                    product.is_recommended = True
                    product.recommended_order = order
                    product.save(
                        update_fields=["is_recommended", "recommended_order", "updated_at"]
                    )

            messages.success(
                request,
                _("Recommended products updated (%(count)s selected).")
                % {"count": len(selected_pks)},
            )
            return redirect(reverse("admin:products_product_recommended"))

        products = list(product_qs)
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": _("Recommended products"),
            "products": products,
            "selected_ids": {p.pk for p in products if p.is_recommended},
        }
        return render(request, "admin/products/product/recommended_products.html", context)

    def promo_sales_view(self, request: HttpRequest) -> HttpResponse:
        if not self.has_change_permission(request):
            return redirect("admin:index")

        product_qs = self._product_admin_queryset(request)
        promo_url = reverse("admin:products_product_promo_sales")

        if request.method == "POST":
            action = request.POST.get("action")
            selected_ids = self._parse_product_ids(request.POST.getlist("products"))

            if not selected_ids:
                messages.warning(request, _("No products selected."))
                return redirect(promo_url)

            selected_products = list(product_qs.filter(pk__in=selected_ids))

            if action == "remove":
                removed = 0
                now = timezone.now()
                for product in selected_products:
                    if not product.has_discount:
                        continue
                    product.discount_price = None
                    product.updated_at = now
                    product.save(update_fields=["discount_price", "updated_at"])
                    removed += 1

                if removed:
                    messages.success(
                        request,
                        _("Promo removed from %(count)s products.")
                        % {"count": removed},
                    )
                else:
                    messages.info(
                        request,
                        _("None of the selected products had an active promo price."),
                    )
                return redirect(promo_url)

            if action == "apply":
                form = PromoSaleForm(request.POST)
                if form.is_valid():
                    percent = form.cleaned_data.get("discount_percent")
                    if percent is None:
                        form.add_error(
                            "discount_percent",
                            _("Enter a discount percent to apply a promo sale."),
                        )
                    else:
                        multiplier = (Decimal("100") - percent) / Decimal("100")
                        updated = 0
                        skipped = 0
                        for product in selected_products:
                            new_price = (product.price * multiplier).quantize(
                                Decimal("0.01"),
                                rounding=ROUND_HALF_UP,
                            )
                            if new_price >= product.price:
                                skipped += 1
                                continue
                            product.discount_price = new_price
                            product.save(
                                update_fields=["discount_price", "updated_at"]
                            )
                            updated += 1

                        if updated:
                            messages.success(
                                request,
                                _("Promo sale updated for %(count)s products.")
                                % {"count": updated},
                            )
                        if skipped:
                            messages.warning(
                                request,
                                _(
                                    "%(count)s products skipped because promo price was not lower than regular price."
                                )
                                % {"count": skipped},
                            )
                        if updated or skipped:
                            return redirect(promo_url)

        else:
            form = PromoSaleForm()

        products = list(product_qs)
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": _("Promo sales"),
            "form": form,
            "products": products,
            "promo_product_ids": {p.pk for p in products if p.has_discount},
        }
        return render(request, "admin/products/product/promo_sales.html", context)

    @staticmethod
    def _parse_product_ids(raw_ids: list[str]) -> list[int]:
        parsed: list[int] = []
        for raw in raw_ids:
            try:
                parsed.append(int(raw))
            except (TypeError, ValueError):
                continue
        return parsed

    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj, **kwargs)

        def autofill_slug_for_translation(trans, master):
            return unique_slug_for_translation(trans, fallback=master.sku)

        form_class.autofill_slug_for_translation = autofill_slug_for_translation
        return form_class

    @admin.display(description=_("Product image"))
    def photo_preview(self, obj):
        if obj.main_image:
            return format_html('<img class="kp-product-thumb" src="{}" alt="" width="48" height="48" loading="lazy">', obj.main_image.url)
        return format_html('<span class="kp-product-thumb kp-product-thumb--empty" title="{}">—</span>', _("Without photo"))

    @admin.display(description=_("Slug"))
    def slug_display(self, obj: Product) -> str:
        return slug_warning_cell(localized_slug(obj))

    @admin.display(description=_("Price"))
    def price_display(self, obj: Product) -> str:
        return price_cell(
            obj.effective_price,
            base=obj.price,
            has_discount=obj.has_discount,
        )

    @admin.display(description=_("Stock"))
    def stock_display(self, obj: Product) -> str:
        return stock_cell(
            obj.stock,
            is_low=obj.is_low_stock,
            alert_at=obj.minimum_stock_alert,
        )
