import json
import uuid
from decimal import Decimal

from django.test import Client, TestCase

from apps.cart.cart import SESSION_KEY, get_cart
from apps.categories.models import Category
from apps.core.storefront_urls import shop_reverse
from apps.products.models import Product


class CartUpdateViewTests(TestCase):
    def setUp(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        self.category = Category.objects.create(is_active=True)
        self.category.set_current_language("sr")
        self.category.name = "Kat"
        self.category.slug = f"kat-{suffix}"
        self.category.save()

        self.product = Product.objects.create(
            category=self.category,
            sku=f"SKU-CART-{suffix}",
            price=Decimal("500.00"),
            stock=5,
        )
        self.product.set_current_language("sr")
        self.product.name = "Cart product"
        self.product.slug = f"cart-{suffix}"
        self.product.save()

        self.client = Client()
        session = self.client.session
        session[SESSION_KEY] = {str(self.product.pk): 1}
        session.save()

    def test_cart_update_returns_json_totals(self) -> None:
        url = shop_reverse("cart:update", product_id=self.product.pk)
        response = self.client.post(
            url,
            {"quantity": 3},
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["subtotal"], "1500.00")
        self.assertEqual(payload["item_count"], 3)
        self.assertEqual(payload["lines"][0]["quantity"], 3)
        self.assertEqual(payload["lines"][0]["line_total"], "1500.00")

    def test_cart_remove_returns_json(self) -> None:
        url = shop_reverse("cart:remove", product_id=self.product.pk)
        response = self.client.post(
            url,
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["item_count"], 0)
        self.assertEqual(payload["lines"], [])

    def test_cart_state_includes_remove_url(self) -> None:
        response = self.client.get(
            shop_reverse("cart:state"),
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertTrue(payload["ok"])
        self.assertIn("remove_url", payload["lines"][0])

    def test_cart_update_json_rejects_over_stock(self) -> None:
        url = shop_reverse("cart:update", product_id=self.product.pk)
        response = self.client.post(
            url,
            {"quantity": 99},
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        payload = json.loads(response.content)
        self.assertFalse(payload["ok"])
        self.assertIn("error", payload)

    def test_cart_page_includes_live_update_script(self) -> None:
        response = self.client.get(shop_reverse("cart:detail"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-cart-page")
        self.assertContains(response, "cart.js")
        self.assertNotContains(response, "shop-cart-line__update")

    def test_failed_quantity_edit_returns_saved_cart_without_mutating_it(self) -> None:
        for quantity in ("2.5", "", "no", "-1", "99"):
            with self.subTest(quantity=quantity):
                response = self.client.post(
                    shop_reverse("cart:update", product_id=self.product.pk),
                    {"quantity": quantity}, HTTP_ACCEPT="application/json",
                )
                self.assertEqual(response.status_code, 400)
                payload = response.json()
                self.assertFalse(payload["ok"])
                self.assertEqual(payload["lines"][0]["quantity"], 1)
                self.assertEqual(payload["subtotal"], "500.00")
                self.assertEqual(self.client.session[SESSION_KEY][str(self.product.pk)], 1)

    def test_zero_quantity_still_removes_line_and_announces_result(self) -> None:
        response = self.client.post(
            shop_reverse("cart:update", product_id=self.product.pk),
            {"quantity": 0}, HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["lines"], [])
        self.assertTrue(response.json()["message"])

    def test_cart_has_no_javascript_save_and_live_empty_state(self) -> None:
        response = self.client.get(shop_reverse("cart:detail"))
        self.assertContains(response, 'type="submit" class="shop-btn shop-btn--ghost shop-btn--sm" data-cart-save')
        self.assertContains(response, 'data-cart-empty hidden')
        self.assertContains(response, 'data-cart-load-error hidden')
        self.assertContains(response, 'data-cart-quantity-form')
        self.assertContains(response, 'data-cart-remove-form')


class CartAddViewTests(TestCase):
    def setUp(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        category = Category.objects.create(is_active=True)
        category.set_current_language("sr")
        category.name = "Kat"
        category.slug = f"kat-add-{suffix}"
        category.save()

        self.product = Product.objects.create(
            category=category,
            sku=f"SKU-ADD-{suffix}",
            price=Decimal("500.00"),
            stock=5,
        )
        self.product.set_current_language("sr")
        self.product.name = "Add product"
        self.product.slug = f"add-{suffix}"
        self.product.save()

    def test_add_from_list_with_quantity(self) -> None:
        response = self.client.post(
            shop_reverse("cart:add"),
            {
                "product_id": self.product.pk,
                "quantity": 3,
                "next": shop_reverse("products:list"),
            },
        )
        self.assertEqual(response.status_code, 302)
        cart = get_cart(self.client)
        lines = cart.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].quantity, 3)
        self.assertEqual(lines[0].product.pk, self.product.pk)

    def test_add_returns_json_without_redirect(self) -> None:
        response = self.client.post(
            shop_reverse("cart:add"),
            {"product_id": self.product.pk, "quantity": 2},
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["item_count"], 2)
        self.assertIn("message", payload)
        self.assertEqual(payload["product_id"], self.product.pk)
        cart = get_cart(self.client)
        self.assertEqual(cart.total_items, 2)

    def test_cart_state_returns_line_details(self) -> None:
        self.client.post(
            shop_reverse("cart:add"),
            {"product_id": self.product.pk, "quantity": 2},
        )
        response = self.client.get(
            shop_reverse("cart:state"),
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["item_count"], 2)
        self.assertEqual(len(payload["lines"]), 1)
        line = payload["lines"][0]
        self.assertEqual(line["product_id"], self.product.pk)
        self.assertEqual(line["quantity"], 2)
        self.assertIn("name", line)
        self.assertIn("url", line)
        self.assertIn("update_url", line)
        self.assertIn("unit_price_display", line)

    def test_add_json_rejects_over_stock(self) -> None:
        response = self.client.post(
            shop_reverse("cart:add"),
            {"product_id": self.product.pk, "quantity": 99},
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        payload = json.loads(response.content)
        self.assertFalse(payload["ok"])

    def test_invalid_add_quantity_does_not_silently_add_one(self) -> None:
        for quantity in ("2.5", "", "no", "0", "-1"):
            with self.subTest(quantity=quantity):
                response = self.client.post(
                    shop_reverse("cart:add"),
                    {"product_id": self.product.pk, "quantity": quantity},
                    HTTP_ACCEPT="application/json",
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["lines"], [])
                self.assertEqual(get_cart(self.client).total_items, 0)

    def test_missing_product_json_is_actionable_and_does_not_change_cart(self) -> None:
        response = self.client.post(
            shop_reverse("cart:add"), {"product_id": "invalid", "quantity": 1},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()["ok"])
        self.assertTrue(response.json()["error"])
        self.assertEqual(response.json()["lines"], [])

    def test_add_fallback_does_not_redirect_to_an_external_next_url(self) -> None:
        response = self.client.post(
            shop_reverse("cart:add"),
            {"product_id": self.product.pk, "quantity": 1, "next": "https://example.org/"},
        )
        self.assertRedirects(response, shop_reverse("cart:detail"))
