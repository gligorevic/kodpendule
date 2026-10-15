import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.core.storefront_urls import shop_reverse
from apps.orders.models import Order, OrderStatus
from apps.orders.services.order_access import SESSION_KEY
from apps.shipping.models import City

User = get_user_model()


class OrderTrackingTests(TestCase):
    def setUp(self) -> None:
        self.city = City.objects.create(
            name="Beograd",
            slug="beograd",
            shipping_price=Decimal("350.00"),
            is_active=True,
        )
        suffix = uuid.uuid4().hex[:8]
        self.order_number = f"KP-TEST-{suffix}"
        self.guest_email = "guest@example.com"
        self.order = Order.objects.create(
            order_number=self.order_number,
            guest_email=self.guest_email,
            first_name="Pera",
            last_name="Perić",
            phone="+381601112233",
            shipping_street="Ulica 1",
            shipping_city_name="Beograd",
            shipping_city=self.city,
            requested_delivery_date=timezone.localdate(),
            order_notes="Notes",
            shipping_price=Decimal("350.00"),
            subtotal=Decimal("1000.00"),
            total=Decimal("1350.00"),
            status=OrderStatus.PENDING,
        )
        self.user = User.objects.create_user(
            username=f"buyer-{suffix}",
            email="buyer@example.com",
            password="test-pass-123",
        )
        self.user_order_number = f"KP-USER-{suffix}"
        self.user_order = Order.objects.create(
            order_number=self.user_order_number,
            user=self.user,
            guest_email=self.user.email,
            first_name="Ana",
            last_name="Anić",
            phone="+381601112244",
            shipping_street="Ulica 2",
            shipping_city_name="Beograd",
            shipping_city=self.city,
            requested_delivery_date=timezone.localdate(),
            order_notes="User order",
            shipping_price=Decimal("350.00"),
            subtotal=Decimal("500.00"),
            total=Decimal("850.00"),
            status=OrderStatus.CONFIRMED,
        )

    def test_guest_tracks_status_with_number_only_without_personal_details(self):
        response = self.client.post(shop_reverse("orders:track"), {"order_number": self.order_number})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["tracked_order"]["status"], OrderStatus.PENDING)
        self.assertContains(response, self.order_number)
        for private_value in (self.guest_email, "Pera", "Perić", self.order.phone, "Ulica 1", "Notes"):
            self.assertNotContains(response, private_value)
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        detail = self.client.get(shop_reverse("orders:detail", order_number=self.order_number))
        self.assertEqual(detail.status_code, 404)

    def test_tracking_normalizes_case_spaces_and_optional_prefix(self):
        self.order.order_number = "KP-482917"
        self.order.save(update_fields=["order_number"])
        for number in ("  kp-482917  ", "482917", "KP - 482917"):
            response = self.client.post(shop_reverse("orders:track"), {"order_number": number})
            self.assertEqual(response.context["tracked_order"]["order_number"], "KP-482917")

    def test_track_form_has_no_email_or_account_links(self):
        response = self.client.get(shop_reverse("orders:track"))
        self.assertNotContains(response, 'name="email"')
        self.assertNotContains(response, shop_reverse("accounts:login"))
        self.assertNotContains(response, shop_reverse("accounts:register"))

    def test_cancelled_order_shows_cancelled_state(self):
        self.order.status = OrderStatus.CANCELLED
        self.order.save(update_fields=["status"])
        response = self.client.post(shop_reverse("orders:track"), {"order_number": self.order_number})
        self.assertFalse(response.context["show_progress"])
        self.assertEqual(response.context["tracked_order"]["status"], OrderStatus.CANCELLED)

    def test_guest_track_unknown_number_same_error(self) -> None:
        response = self.client.post(
            shop_reverse("orders:track"),
            {
                "order_number": "KP-NO-SUCH-ORDER",
                "email": self.guest_email,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Nismo pronašli narudžbinu",
        )

    def test_guest_detail_without_access_returns_404(self) -> None:
        response = self.client.get(
            shop_reverse("orders:detail", order_number=self.order_number)
        )
        self.assertEqual(response.status_code, 404)

    def test_guest_detail_unknown_number_returns_404_even_with_session(self) -> None:
        session = self.client.session
        session[SESSION_KEY] = [self.order.pk]
        session.save()
        response = self.client.get(
            shop_reverse("orders:detail", order_number="KP-UNKNOWN-999")
        )
        self.assertEqual(response.status_code, 404)

    def test_logged_in_history_and_detail(self) -> None:
        self.client.login(username=self.user.username, password="test-pass-123")
        history = self.client.get(shop_reverse("orders:history"))
        self.assertEqual(history.status_code, 200)
        self.assertContains(history, self.user_order_number)
        self.assertNotContains(history, self.order_number)

        detail = self.client.get(
            shop_reverse(
                "orders:detail",
                order_number=self.user_order_number,
            )
        )
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Ana")

    def test_logged_in_cannot_view_other_guest_order(self) -> None:
        self.client.login(username=self.user.username, password="test-pass-123")
        response = self.client.get(
            shop_reverse("orders:detail", order_number=self.order_number)
        )
        self.assertEqual(response.status_code, 404)

    def test_history_requires_login(self) -> None:
        response = self.client.get(shop_reverse("orders:history"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(shop_reverse("accounts:login"), response["Location"])
