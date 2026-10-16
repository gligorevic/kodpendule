from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.translation import activate

from apps.shipping.models import City


class CityPaymentSettingsAdminTests(TestCase):
    def setUp(self) -> None:
        activate("sr")
        User = get_user_model()
        self.admin = User.objects.create_superuser("admin", "admin@test.com", "pass")
        self.client = Client()
        self.client.force_login(self.admin)
        self.city = City.objects.create(
            name="Beograd",
            slug="beograd",
            shipping_price=Decimal("350.00"),
            is_active=True,
        )

    def test_payment_settings_page_loads(self) -> None:
        response = self.client.get(reverse("admin:shipping_city_payment_settings"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Podešavanja plaćanja")
        self.assertContains(response, "Beograd")

    def test_payment_settings_save_per_city(self) -> None:
        response = self.client.post(
            reverse("admin:shipping_city_payment_settings"),
            {
                "city": str(self.city.pk),
                "promo_cart_threshold": "1500.00",
                "promo_shipping_mode": "discounted",
                "promo_discounted_shipping_price": "199.00",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.city.refresh_from_db()
        self.assertEqual(self.city.promo_cart_threshold, Decimal("1500.00"))
        self.assertEqual(self.city.promo_discounted_shipping_price, Decimal("199.00"))

    def test_staff_without_change_permission_cannot_change_delivery_rules(self):
        from django.contrib.auth.models import Permission
        viewer = get_user_model().objects.create_user(username="delivery-viewer", is_staff=True)
        viewer.user_permissions.add(Permission.objects.get(content_type__app_label="shipping", codename="view_city"))
        self.client.force_login(viewer)
        url = reverse("admin:shipping_city_payment_settings")
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {"city": self.city.pk, "promo_cart_threshold": "1", "promo_shipping_mode": "free"}).status_code, 403)
        self.city.refresh_from_db()
        self.assertIsNone(self.city.promo_cart_threshold)
