"""Permission-aware shortcuts and the daily work queue for store managers."""
from django.db.models import Count, F, Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from apps.dashboard.selectors import analytics_selectors as analytics
from apps.orders.models import Order
from apps.products.models import Product


def build_admin_home_context(request):
    user = request.user
    if not user.is_active or not user.is_staff:
        return {}
    can_products = user.has_perm("products.view_product") or user.has_perm("products.change_product")
    can_orders = user.has_perm("orders.view_order") or user.has_perm("orders.change_order")
    context = {"home_can_products": can_products, "home_can_orders": can_orders}
    actions, attention = [], []
    if can_products:
        url = reverse("admin:products_product_changelist")
        actions.append({"title": _("Products"), "description": _("Search, prices, photos and stock"), "url": url, "icon": "▦"})
        counts = Product.objects.filter(is_archived=False).aggregate(
            total=Count("pk"), missing=Count("pk", filter=Q(main_image="") | Q(main_image__isnull=True)),
            low=Count("pk", filter=Q(stock__lte=F("minimum_stock_alert"))),
        )
        attention.extend([
            {"label": _("Active products"), "count": counts["total"], "url": url + "?is_archived__exact=0"},
            {"label": _("Low stock alerts"), "count": counts["low"], "url": url + "?stock_state=low&is_archived__exact=0"},
            {"label": _("Without photo"), "count": counts["missing"], "url": url + "?photo=missing&is_archived__exact=0"},
        ])
        context["home_low_stock"] = analytics.low_stock_products(limit=6)
    if user.has_perm("products.change_product"):
        actions.append({"title": _("Import inventory XML"), "description": _("Drop a file, review changes, update stock"), "url": reverse("admin:products_product_import_xml"), "icon": "↥"})
    if can_orders:
        url = reverse("admin:orders_order_changelist")
        actions.insert(0, {"title": _("Orders"), "description": _("New orders, delivery and status"), "url": url, "icon": "≡"})
        attention.insert(0, {"label": _("Unread orders"), "count": Order.objects.filter(is_new=True).count(), "url": url + "?is_new__exact=1"})
        context.update(home_overview=analytics.overview_snapshot(), home_recent_orders=Order.objects.select_related("user").order_by("-created_at")[:6])
    if user.has_perm("categories.view_category") or user.has_perm("categories.change_category"):
        actions.append({"title": _("Categories"), "description": _("Organize products and subcategories"), "url": reverse("admin:categories_category_changelist"), "icon": "◫"})
    context.update(home_actions=actions, home_attention=attention)
    return context
