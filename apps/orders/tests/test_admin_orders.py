import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.orders.models import Order
from apps.orders.selectors.order_admin_selectors import unread_order_count
from apps.shipping.models import City


class OrderAdminUnreadTests(TestCase):
    def setUp(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        self.city = City.objects.create(
            name="Beograd",
            slug=f"bg-{suffix}",
            shipping_price=Decimal("300"),
        )
        self.order = Order.objects.create(
            order_number=f"KP-NEW-{suffix}",
            guest_email="guest@example.com",
            first_name="Pera",
            last_name="Perić",
            phone="+381601112233",
            shipping_street="Ulica 1",
            shipping_city_name="Beograd",
            shipping_city=self.city,
            requested_delivery_date=timezone.localdate(),
            shipping_price=Decimal("300"),
            subtotal=Decimal("1000"),
            total=Decimal("1300"),
            is_new=True,
        )
        User = get_user_model()
        self.admin = User.objects.create_superuser("admin", "admin@test.com", "pass")
        self.client = Client()
        self.client.force_login(self.admin)

    def test_new_order_counts_as_unread(self) -> None:
        self.assertEqual(unread_order_count(), 1)

    def test_opening_order_marks_as_read(self) -> None:
        url = reverse("admin:orders_order_change", args=[self.order.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertFalse(self.order.is_new)
        self.assertEqual(unread_order_count(), 0)

    def test_export_selected_orders_csv(self) -> None:
        changelist_url = reverse("admin:orders_order_changelist")
        response = self.client.post(
            changelist_url,
            {
                "action": "export_selected_csv",
                "_selected_action": [str(self.order.pk)],
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8-sig")
        self.assertIn("Broj narudžbine", body.splitlines()[0])
        self.assertIn(self.order.order_number, body)
        self.assertIn("Ulica 1", body)

    def test_new_order_row_is_marked_unread_on_changelist(self) -> None:
        response = self.client.get(reverse("admin:orders_order_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "kp-order-row--new")
        self.assertContains(response, "kp-money--emphasis")

    def test_read_order_row_is_not_bold_on_changelist(self) -> None:
        self.order.is_new = False
        self.order.save(update_fields=["is_new"])
        response = self.client.get(reverse("admin:orders_order_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "kp-order-row--new")
        self.assertNotContains(response, "kp-money--emphasis")

    def test_order_product_choices_do_not_load_the_entire_catalog(self):
        from django.core.cache import cache
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from apps.categories.models import Category
        from apps.products.models import Product
        from apps.orders.models import OrderItem

        category = Category.objects.create(name="Hrana", slug="admin-food")
        selected = Product.objects.create(
            category=category, sku="SELECTED", price=100,
            name="Izabrani proizvod", slug="selected-product",
        )
        for index in range(5):
            OrderItem.objects.create(
                order=self.order, product=selected, product_name="Izabrani proizvod",
                sku=selected.sku, unit_price=100, quantity=1,
            )
        url = reverse("admin:orders_order_change", args=[self.order.pk])
        cache.clear()
        with CaptureQueriesContext(connection) as small:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        for index in range(60):
            Product.objects.create(
                category=category, sku=f"UNRELATED-{index}", price=100,
                name=f"Unrelated catalog product {index}", slug=f"unrelated-{index}",
            )
        cache.clear()
        self.addCleanup(cache.clear)
        with CaptureQueriesContext(connection) as large:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(large), len(small) + 2)
        self.assertContains(response, "Izabrani proizvod")
        self.assertNotContains(response, "Unrelated catalog product")
        self.assertContains(response, "admin-autocomplete")

        lookup = self.client.get(reverse("admin:autocomplete"), {
            "app_label": "orders", "model_name": "orderitem",
            "field_name": "product", "term": "UNRELATED",
        })
        self.assertEqual(lookup.status_code, 200)
        self.assertEqual(len(lookup.json()["results"]), 20)
        self.assertTrue(lookup.json()["pagination"]["more"])
        selected_lookup = self.client.get(reverse("admin:autocomplete"), {
            "app_label": "orders", "model_name": "orderitem",
            "field_name": "product", "term": "SELECTED",
        })
        self.assertEqual(selected_lookup.json()["results"][0]["id"], str(selected.pk))
        self.client.logout()
        self.assertNotEqual(self.client.get(reverse("admin:autocomplete"), {
            "app_label": "orders", "model_name": "orderitem", "field_name": "product",
        }).status_code, 200)
