from django.contrib import messages
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from apps.cart.api import cart_add_json, cart_state_json
from apps.cart.cart import get_cart
from apps.core.mixins import ShopLanguageMixin
from apps.core.storefront_urls import shop_reverse
from apps.core.utils import activate_parler_language, get_shop_language
from apps.products.models import Product
from apps.products.selectors import get_product_by_slug


def _wants_json(request) -> bool:
    accept = request.headers.get("Accept", "")
    return "application/json" in accept or request.headers.get("X-Requested-With") == "XMLHttpRequest"


class CartStateView(View):
    """GET: current cart JSON for mini-cart drawer and live updates."""

    def get(self, request, *args, **kwargs):
        cart = get_cart(request)
        return JsonResponse(cart_state_json(request, cart))


class CartDetailView(ShopLanguageMixin, TemplateView):
    template_name = "cart/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = get_cart(self.request)
        lines = cart.get_lines()
        for line in lines:
            activate_parler_language(line.product, self.shop_language)
        context.update(
            {
                "cart_lines": lines,
                "cart_subtotal": cart.subtotal,
                "cart_item_count": cart.total_items,
                "meta_title": _("Cart"),
                "canonical_url": self.request.build_absolute_uri(),
            }
        )
        return context


class CartAddView(View):
    """POST: add product to cart."""

    def post(self, request, *args, **kwargs):
        cart = get_cart(request)
        product = None
        if "product_id" in request.POST:
            product = get_object_or_404(
                Product.objects.filter(is_archived=False),
                pk=request.POST.get("product_id"),
            )
        elif "slug" in kwargs:
            product = get_product_by_slug(kwargs["slug"])
            if product is None:
                raise Http404

        if product is None:
            if _wants_json(request):
                return JsonResponse(
                    {"ok": False, "error": str(_("Product not found."))},
                    status=404,
                )
            messages.error(request, _("Product not found."))
            return redirect(shop_reverse("products:list"))

        if product.stock < 1:
            if _wants_json(request):
                return JsonResponse(
                    {"ok": False, "error": str(_("This product is out of stock."))},
                    status=400,
                )
            messages.error(request, _("This product is out of stock."))
            return redirect(product.get_absolute_url())

        try:
            qty = int(request.POST.get("quantity", 1))
        except (TypeError, ValueError):
            qty = 1
        qty = max(1, qty)

        try:
            cart.add(product, qty)
        except ValueError:
            if _wants_json(request):
                return JsonResponse(
                    {"ok": False, "error": str(_("Not enough items in stock."))},
                    status=400,
                )
            messages.error(request, _("Not enough items in stock."))
            return redirect(product.get_absolute_url())

        if _wants_json(request):
            return JsonResponse(cart_add_json(request, cart, product))

        product.set_current_language(get_shop_language(request))
        messages.success(
            request,
            _("“%(name)s” added to cart.")
            % {"name": product.safe_translation_getter("name", any_language=True)},
        )
        next_url = request.POST.get("next") or shop_reverse("cart:detail")
        return HttpResponseRedirect(next_url)


class CartUpdateView(View):
    def post(self, request, *args, **kwargs):
        cart = get_cart(request)
        product = get_object_or_404(
            Product.objects.all(),
            pk=kwargs["product_id"],
        )
        try:
            qty = int(request.POST.get("quantity", 1))
        except (TypeError, ValueError):
            qty = 1
        try:
            cart.set_quantity(product, qty)
        except ValueError:
            if _wants_json(request):
                return JsonResponse(
                    {"ok": False, "error": str(_("Not enough items in stock."))},
                    status=400,
                )
            messages.error(request, _("Not enough items in stock."))
            return redirect(shop_reverse("cart:detail"))

        if _wants_json(request):
            return JsonResponse(cart_state_json(request, cart))

        messages.success(request, _("Cart updated."))
        return redirect(shop_reverse("cart:detail"))


class CartRemoveView(View):
    def post(self, request, *args, **kwargs):
        cart = get_cart(request)
        product = get_object_or_404(Product, pk=kwargs["product_id"])
        cart.remove(product)
        if _wants_json(request):
            return JsonResponse(cart_state_json(request, cart))
        messages.info(request, _("Item removed from cart."))
        return redirect(shop_reverse("cart:detail"))
