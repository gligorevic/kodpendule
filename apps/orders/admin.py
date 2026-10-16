from django import forms
from django.contrib import admin, messages
from django.http import HttpResponse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.core.admin_display import money_cell, order_status_badge
from apps.core.locale_dates import latin_short_datetime
from apps.core.kp_admin import KPModelAdmin
from apps.orders.models import Order, OrderItem, OrderStatus
from apps.orders.services.order_csv import export_orders_csv


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    # Loading every product for each order line can exhaust the worker timeout.
    autocomplete_fields = ("product",)
    extra = 0
    verbose_name = _("Order item")
    verbose_name_plural = _("Order items")
    readonly_fields = ("product_name", "sku", "unit_price", "line_total_display")
    fields = (
        "product",
        "product_name",
        "sku",
        "unit_price",
        "quantity",
        "line_total_display",
    )
    classes = ("kp-inline-order-items",)

    @admin.display(description=_("Line total"))
    def line_total_display(self, obj: OrderItem) -> str:
        if obj.pk:
            return money_cell(obj.line_total, emphasize=True)
        return "—"


@admin.register(Order)
class OrderAdmin(KPModelAdmin):
    list_display = (
        "order_number",
        "customer_display",
        "delivery_display",
        "status_badge",
        "total_display",
        "payment_method",
        "created_at_display",
    )
    search_fields = (
        "order_number",
        "guest_email",
        "first_name",
        "last_name",
        "phone",
        "shipping_street",
        "shipping_city_name",
        "user__email",
        "user__username",
    )
    readonly_fields = ("created_at", "updated_at", "is_new", "age_confirmed_at")
    list_select_related = ("user", "shipping_city")
    list_filter = ("is_new", "status")
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"
    list_per_page = 25
    save_on_top = True
    fieldsets = (
        (
            _("Order"),
            {
                "classes": ("kp-fieldset", "kp-fieldset--order-core"),
                "description": _(
                    "Update order status when you confirm, ship, or complete the order."
                ),
                "fields": (
                    "order_number",
                    "user",
                    "guest_email",
                    "status",
                    "is_new",
                    "payment_method",
                    "age_confirmed_at",
                ),
            },
        ),
        (
            _("Customer"),
            {
                "classes": ("kp-fieldset", "kp-fieldset--customer"),
                "fields": ("first_name", "last_name", "phone"),
            },
        ),
        (
            _("Shipping"),
            {
                "classes": ("kp-fieldset", "kp-fieldset--shipping"),
                "fields": (
                    "shipping_street",
                    "shipping_city_name",
                    "shipping_city",
                    "requested_delivery_date",
                    "shipping_price",
                    "order_notes",
                ),
            },
        ),
        (
            _("Totals"),
            {
                "classes": ("kp-fieldset", "kp-fieldset--totals"),
                "description": _("Amounts charged to the customer."),
                "fields": ("subtotal", "total"),
            },
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "status" and formfield:
            formfield.widget = forms.Select(
                attrs={
                    **formfield.widget.attrs,
                    "class": "kp-status-select",
                },
                choices=formfield.choices,
            )
        return formfield

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user", "shipping_city")
            .prefetch_related("items")
        )

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if object_id and request.method == "GET":
            Order.objects.filter(pk=object_id, is_new=True).update(is_new=False)
        return super().changeform_view(request, object_id, form_url, extra_context)

    @admin.action(description=_("Export selected to CSV"))
    def export_selected_csv(self, request, queryset):
        if not queryset.exists():
            self.message_user(request, _("No orders selected."), level=messages.WARNING)
            return None

        stamp = timezone.localdate().strftime("%Y%m%d")
        response = HttpResponse(
            export_orders_csv(queryset.select_related("user", "shipping_city")),
            content_type="text/csv; charset=utf-8",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="orders-{stamp}.csv"'
        )
        return response

    @admin.action(description=_("Mark as confirmed"))
    def mark_confirmed(self, request, queryset):
        queryset.update(status=OrderStatus.CONFIRMED)

    @admin.action(description=_("Mark as shipped"))
    def mark_shipped(self, request, queryset):
        queryset.update(status=OrderStatus.SHIPPED)

    @admin.action(description=_("Mark as delivered"))
    def mark_delivered(self, request, queryset):
        queryset.update(status=OrderStatus.DELIVERED)

    actions = [
        "export_selected_csv",
        "mark_confirmed",
        "mark_shipped",
        "mark_delivered",
    ]

    @admin.display(description=_("Status"))
    def status_badge(self, obj: Order) -> str:
        return order_status_badge(obj.status)

    @admin.display(description=_("Total"))
    def total_display(self, obj: Order) -> str:
        return money_cell(obj.total, emphasize=obj.is_new)

    @admin.display(description=_("Delivery"))
    def delivery_display(self, obj: Order) -> str:
        address = obj.delivery_address_display
        return address or "—"

    @admin.display(description=_("Created at"), ordering="created_at")
    def created_at_display(self, obj: Order) -> str:
        return latin_short_datetime(obj.created_at)

    @admin.display(description=_("Customer"))
    def customer_display(self, obj: Order) -> str:
        name = obj.customer_full_name
        if obj.is_guest_order:
            return format_html(
                '{} <span class="kp-guest-tag">({})</span>',
                name,
                _("guest"),
            )
        return name
