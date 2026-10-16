from __future__ import annotations

import logging

from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView

from apps.cart.cart import get_cart
from apps.categories.age_confirmation import requires_age_confirmation
from apps.checkout.forms import CheckoutForm
from apps.core.mixins import ShopLanguageMixin
from apps.core.storefront_urls import shop_reverse, shop_reverse_lazy
from apps.core.utils import activate_parler_language
from apps.orders.selectors import order_detail_qs
from apps.orders.services import (
    CheckoutError,
    create_order_from_checkout,
    notify_customer_new_order,
    notify_staff_new_order,
)
from apps.orders.services.order_access import grant_order_access
from apps.core.checkout_settings import checkout_today, min_scheduled_delivery_date, resolve_checkout_shipping_price
from apps.shipping.selectors import active_cities

logger = logging.getLogger(__name__)


class CheckoutView(ShopLanguageMixin, FormView):
    template_name = "checkout/checkout.html"
    form_class = CheckoutForm
    success_url = shop_reverse_lazy("checkout:success")

    def dispatch(self, request, *args, **kwargs):
        cart = get_cart(request)
        if cart.is_empty:
            messages.warning(request, _("Your cart is empty."))
            return redirect(shop_reverse("products:list"))
        if not active_cities().exists():
            messages.error(
                request,
                _("Delivery is not available yet. Please contact us."),
            )
            return redirect(shop_reverse("core:contact"))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["requires_age_confirmation"] = requires_age_confirmation(
            line.product for line in get_cart(self.request).get_lines()
        )
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        user = self.request.user
        if user.is_authenticated:
            initial.setdefault("first_name", user.first_name)
            initial.setdefault("last_name", user.last_name)
            profile = getattr(user, "profile", None)
            if profile:
                initial.setdefault("phone", profile.phone)
        return initial

    def _city_delivery_context(self, cities) -> dict:
        return {
            str(city.pk): {
                "base": str(city.shipping_price),
                "threshold": str(city.promo_cart_threshold)
                if city.promo_cart_threshold
                else "",
                "discounted_shipping_price": str(city.promo_discounted_shipping_price)
                if city.promo_discounted_shipping_price is not None
                else "",
                "threshold_shipping_mode": city.promo_shipping_mode,
            }
            for city in cities
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = get_cart(self.request)
        lines = cart.get_lines()
        for line in lines:
            activate_parler_language(line.product, self.shop_language)
        cities = list(active_cities())
        city_delivery = self._city_delivery_context(cities)
        context.update(
            {
                "cart_lines": lines,
                "cart_subtotal": cart.subtotal,
                "cities": cities,
                "city_delivery": city_delivery,
                "has_promo_delivery_threshold": any(
                    city.promo_cart_threshold for city in cities
                ),
                "checkout_today": checkout_today().isoformat(),
                "min_scheduled_delivery_date": min_scheduled_delivery_date().isoformat(),
                "is_guest": not self.request.user.is_authenticated,
                "meta_title": _("Checkout"),
                "canonical_url": self.request.build_absolute_uri(),
            }
        )
        cleaned = getattr(context["form"], "cleaned_data", {})
        city = cleaned.get("shipping_city")
        delivery_date = cleaned.get("requested_delivery_date")
        if city and cleaned.get("delivery_timing") and delivery_date:
            shipping = resolve_checkout_shipping_price(
                subtotal=cart.subtotal, city=city, requested_delivery_date=delivery_date
            )
            context["checkout_shipping"] = shipping
            context["checkout_total"] = cart.subtotal + shipping
        return context

    def get_success_url(self):
        return shop_reverse("checkout:success", language=self.shop_language)

    def form_valid(self, form):
        cart = get_cart(self.request)
        try:
            order = create_order_from_checkout(
                cart=cart,
                user=self.request.user,
                guest_email=form.cleaned_data["guest_email"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                phone=form.cleaned_data["phone"],
                shipping_city=form.cleaned_data["shipping_city"],
                shipping_street=form.cleaned_data["shipping_street"],
                order_notes=form.cleaned_data["order_notes"],
                payment_method=form.cleaned_data["payment_method"],
                requested_delivery_date=form.cleaned_data["requested_delivery_date"],
                age_confirmed=form.cleaned_data.get("confirm_age", False),
            )
        except CheckoutError as exc:
            return self.render_to_response(self.get_context_data(form=form, checkout_error=exc.message))
        except Exception:
            logger.exception("Unexpected checkout failure")
            return self.render_to_response(self.get_context_data(
                form=form,
                checkout_error=_("We could not place your order. Please try again or contact us."),
            ))

        self.request.session["last_order_number"] = order.order_number
        self.request.session["last_order_id"] = order.pk
        grant_order_access(self.request, order)
        notify_customer_new_order(order)
        notify_staff_new_order(order)
        logger.info("Order placed: %s", order.order_number)
        messages.success(
            self.request,
            _("Thank you! Your order %(number)s has been placed.")
            % {"number": order.order_number},
        )
        return super().form_valid(form)


class CheckoutSuccessView(ShopLanguageMixin, TemplateView):
    template_name = "checkout/success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_number = self.request.session.pop("last_order_number", None)
        order_id = self.request.session.pop("last_order_id", None)
        order = None
        if order_id:
            order = order_detail_qs().filter(pk=order_id).first()
        context.update(
            {
                "order_number": order_number,
                "order": order,
                "meta_title": _("Order confirmed"),
                "canonical_url": self.request.build_absolute_uri(),
            }
        )
        return context
