import uuid
from decimal import Decimal

from django.http import Http404
from django.test import RequestFactory, TestCase

from apps.categories.models import Category
from apps.core.tests.test_utils import apply_request_middleware
from apps.products.models import Product
from apps.products.selectors import get_product_by_slug, search_products
from apps.products.selectors import active_products_qs
from apps.core.storefront_urls import shop_reverse
from apps.products.views import ProductDetailView, ProductListView


class ProductViewTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        suffix = uuid.uuid4().hex[:8]
        self.product_slug = f"proizvod-{suffix}"

        self.category = Category.objects.create(is_active=True)
        self.category.set_current_language("sr")
        self.category.name = "Kategorija"
        self.category.slug = f"kategorija-{suffix}"
        self.category.save()

        self.product = Product.objects.create(
            category=self.category,
            sku=f"SKU-{suffix}",
            price=Decimal("1000.00"),
            stock=10,
        )
        self.product.set_current_language("sr")
        self.product.name = "Proizvod test"
        self.product.slug = self.product_slug
        self.product.save()

    def _get(self, view_class, path: str, **kwargs):
        request = self.factory.get(path)
        apply_request_middleware(request)
        return view_class.as_view()(request, **kwargs)

    def test_product_list_returns_200(self) -> None:
        response = self._get(ProductListView, "/proizvodi/")
        self.assertEqual(response.status_code, 200)

    def test_product_list_shows_quantity_on_cards(self) -> None:
        from django.test import Client

        from apps.core.storefront_urls import shop_reverse

        response = Client().get(shop_reverse("products:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'id="qty-card-{self.product.pk}"')
        self.assertContains(response, 'name="quantity"')
        self.assertContains(response, 'data-shop-qty')

    def test_product_detail_by_slug(self) -> None:
        response = self._get(
            ProductDetailView,
            f"/proizvodi/{self.product_slug}/",
            slug=self.product_slug,
        )
        self.assertEqual(response.status_code, 200)

    def test_product_detail_404_for_unknown_slug(self) -> None:
        with self.assertRaises(Http404):
            self._get(
                ProductDetailView,
                "/proizvodi/nepostojeci/",
                slug="nepostojeci",
            )

    def test_search_selector_finds_product(self) -> None:
        results = search_products("Proizvod", "sr")
        self.assertEqual(results.count(), 1)

    def test_get_product_by_slug(self) -> None:
        product = get_product_by_slug(self.product_slug, "sr")
        self.assertIsNotNone(product)
        self.assertEqual(product.sku, self.product.sku)

    def test_archived_product_hidden_and_can_be_restored(self) -> None:
        self.product.is_archived = True
        self.product.save(update_fields=["is_archived", "updated_at"])
        self.assertFalse(active_products_qs().filter(pk=self.product.pk).exists())
        self.assertIsNone(get_product_by_slug(self.product_slug, "sr"))
        self.assertNotContains(self.client.get(shop_reverse("products:list")), f'id="qty-card-{self.product.pk}"')
        self.assertEqual(self.client.get(self.product.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.post(shop_reverse("cart:add"), {"product_id": self.product.pk, "quantity": 1}).status_code, 404)
        self.assertEqual(self.client.post(
            shop_reverse("cart:add"),
            {"product_id": self.product.pk, "quantity": 1},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        ).status_code, 404)
        self.product.is_archived = False
        self.product.save(update_fields=["is_archived", "updated_at"])
        self.assertTrue(active_products_qs().filter(pk=self.product.pk).exists())
        self.assertIsNotNone(get_product_by_slug(self.product_slug, "sr"))
