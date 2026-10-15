import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.core.storefront_urls import shop_reverse

from apps.categories.models import Category
from apps.products.models import Product
from apps.products.selectors import recommended_products_qs


class RecommendedProductsTests(TestCase):
    def setUp(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        self.category = Category.objects.create(is_active=True)
        self.category.set_current_language("sr")
        self.category.name = "Kat"
        self.category.slug = f"kat-{suffix}"
        self.category.save()

        self.product_a = self._create_product(f"A-{suffix}", recommended=True, order=0)
        self.product_b = self._create_product(f"B-{suffix}", recommended=True, order=1)
        self.product_c = self._create_product(f"C-{suffix}", recommended=False, order=0)

    def _create_product(self, sku: str, *, recommended: bool, order: int) -> Product:
        product = Product.objects.create(
            category=self.category,
            sku=sku,
            price=Decimal("1000.00"),
            stock=5,
            is_recommended=recommended,
            recommended_order=order,
        )
        product.set_current_language("sr")
        product.name = f"Product {sku}"
        product.slug = f"product-{sku.lower()}"
        product.save()
        return product

    def test_recommended_selector_filters_and_orders(self) -> None:
        products = list(recommended_products_qs("sr"))
        self.assertEqual(len(products), 2)
        self.assertEqual(products[0].pk, self.product_a.pk)
        self.assertEqual(products[1].pk, self.product_b.pk)

    def test_admin_recommended_view_updates_flags(self) -> None:
        User = get_user_model()
        admin = User.objects.create_superuser("admin", "a@test.com", "pass")
        client = Client()
        client.force_login(admin)

        url = reverse("admin:products_product_recommended")
        response = client.post(
            url,
            {"recommended": [str(self.product_c.pk)]},
        )
        self.assertEqual(response.status_code, 302)

        self.product_a.refresh_from_db()
        self.product_b.refresh_from_db()
        self.product_c.refresh_from_db()
        self.assertFalse(self.product_a.is_recommended)
        self.assertFalse(self.product_b.is_recommended)
        self.assertTrue(self.product_c.is_recommended)
        self.assertEqual(self.product_c.recommended_order, 0)

    def test_home_shows_recommended_carousel(self) -> None:
        response = self.client.get(shop_reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "home-section-recommended")
        self.assertContains(response, "data-product-carousel")
        self.assertContains(response, self.product_a.name)

    def test_home_shows_promo_carousel_when_discounted(self) -> None:
        self.product_a.discount_price = Decimal("800.00")
        self.product_a.save()
        response = self.client.get(shop_reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "home-section-promo-sale")
        content = response.content.decode()
        self.assertGreaterEqual(content.count("data-product-carousel"), 2)

    def test_recommended_list_page(self) -> None:
        response = self.client.get(shop_reverse("products:recommended"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Preporučeni proizvodi")
        self.assertContains(response, self.product_a.name)
        self.assertNotContains(response, self.product_c.name)

    def test_promo_list_page(self) -> None:
        self.product_c.discount_price = Decimal("700.00")
        self.product_c.save()
        response = self.client.get(shop_reverse("products:promo"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Promo akcije")
        self.assertContains(response, self.product_c.name)
        self.assertNotContains(response, self.product_b.name)

    def test_header_nav_promo_and_recommended_links(self) -> None:
        self.product_a.discount_price = Decimal("800.00")
        self.product_a.save()
        response = self.client.get(shop_reverse("core:home"))
        self.assertContains(response, shop_reverse("products:promo"))
        self.assertContains(response, shop_reverse("products:recommended"))
        html = response.content.decode()
        nav_start = html.find("shop-header__nav-list")
        self.assertGreater(nav_start, 0)
        nav_end = html.find("</ul>", nav_start)
        nav_html = html[nav_start:nav_end]
        self.assertNotIn(shop_reverse("core:terms"), nav_html)
        self.assertNotIn(shop_reverse("core:privacy"), nav_html)

    def test_header_hides_empty_promo_link(self) -> None:
        response = self.client.get(shop_reverse("core:home"))
        html = response.content.decode()
        nav_start = html.find("shop-header__nav-list")
        nav_html = html[nav_start:html.find("</ul>", nav_start)]
        self.assertNotIn(shop_reverse("products:promo"), nav_html)
        self.assertIn(shop_reverse("products:recommended"), nav_html)

    def test_navigation_flags_ignore_archived_recommendations_and_invalid_discounts(self) -> None:
        self.product_a.is_archived = True
        self.product_a.discount_price = Decimal("800.00")
        self.product_a.save()
        self.product_b.is_archived = True
        self.product_b.save()
        self.product_c.discount_price = self.product_c.price
        self.product_c.save()

        response = self.client.get(shop_reverse("core:home"))
        self.assertFalse(response.context["has_promo_products"])
        self.assertFalse(response.context["has_recommended_products"])
        self.assertNotContains(response, f'href="{shop_reverse("products:promo")}"')
        self.assertNotContains(response, f'href="{shop_reverse("products:recommended")}"')

        # An archived recommendation becomes a real destination again on restore.
        self.product_a.is_archived = False
        self.product_a.save()
        restored = self.client.get(shop_reverse("core:home"))
        self.assertTrue(restored.context["has_promo_products"])
        self.assertTrue(restored.context["has_recommended_products"])
