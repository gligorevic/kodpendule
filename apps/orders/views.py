from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, FormView, ListView

from apps.core.mixins import ShopLanguageMixin
from apps.orders.forms import GuestOrderTrackForm
from apps.orders.models import Order
from apps.orders.selectors.order_selectors import (
    get_order_for_guest_tracking,
    order_detail_qs,
    orders_for_user,
)
from apps.orders.services.order_access import user_can_view_order
from apps.orders.status_display import order_status_context


class GuestOrderTrackView(ShopLanguageMixin, FormView):
    """Public order progress by number, without exposing customer details."""

    template_name = "orders/track.html"
    form_class = GuestOrderTrackForm

    def get_initial(self):
        initial = super().get_initial()
        order_number = self.request.GET.get("order_number", "").strip()
        if order_number:
            initial["order_number"] = order_number
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "meta_title": _("Track your order"),
                "canonical_url": self.request.build_absolute_uri(),
            }
        )
        return context

    def form_valid(self, form):
        order = get_order_for_guest_tracking(
            form.cleaned_data["order_number"],
        )
        if order is None:
            form.add_error(
                None,
                _(
                    "We could not find that order. Check the number in your confirmation and try again."
                ),
            )
            return self.form_invalid(form)
        return self.render_to_response(self.get_context_data(
            form=form, tracked_order=order, **order_status_context(order["status"])
        ))

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response["Cache-Control"] = "private, no-store"
        response["X-Robots-Tag"] = "noindex, nofollow"
        return response


class OrderDetailView(ShopLanguageMixin, DetailView):
    """Order detail for guests (after checkout) or logged-in owners."""

    model = Order
    template_name = "orders/detail.html"
    context_object_name = "order"
    slug_field = "order_number"
    slug_url_kwarg = "order_number"

    def get_queryset(self):
        return order_detail_qs()

    def get_object(self, queryset=None):
        order = super().get_object(queryset)
        if not user_can_view_order(self.request, order):
            raise Http404
        return order

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = context["order"]
        context.update(
            {
                "meta_title": _("Order %(number)s")
                % {"number": order.order_number},
                "canonical_url": self.request.build_absolute_uri(),
                **order_status_context(order.status),
            }
        )
        return context


class OrderHistoryView(LoginRequiredMixin, ShopLanguageMixin, ListView):
    """Logged-in customer order list."""

    template_name = "orders/history.html"
    context_object_name = "orders"
    paginate_by = 15

    def get_queryset(self):
        return orders_for_user(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "meta_title": _("My orders"),
                "canonical_url": self.request.build_absolute_uri(),
            }
        )
        return context
