import html
import re
import uuid
from decimal import Decimal
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.conf import settings
from django.test import TestCase
from django.utils import translation
from django.utils.text import slugify

from apps.categories.models import Category
from apps.core.storefront_urls import shop_reverse
from apps.products.models import Product, ProductImage
from apps.products.views import ProductListView


class CatalogControlsTests(TestCase):
    def setUp(self):
        self.addCleanup(translation.deactivate)
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        self.suffix = uuid.uuid4().hex[:8]
        self.root = self.category("Food")
        self.child = self.category("Drinks", parent=self.root)
        self.other = self.category("Other")
        self.tea = self.product("Tea leaf", self.child, price="100", discount_price=Decimal("50"), barcode=f"123{self.suffix}")
        self.parent_tea = self.product("Tea bag", self.root, price="80")
        self.coffee = self.product("Coffee", self.child, price="60", stock=0)
        self.outside_tea = self.product("Tea elsewhere", self.other, price="10")
        self.archived = self.product("Tea archived", self.child, is_archived=True)
        self.url = shop_reverse("products:list", language="en")

    def category(self, name, **kwargs):
        category = Category.objects.create(**kwargs)
        category.set_current_language("sr")
        category.name = name
        category.slug = f"{name.lower()}-{self.suffix}"
        category.save()
        return category

    def product(self, name, category, *, price="100", stock=4, **kwargs):
        product = Product.objects.create(category=category, sku=f"{name}-{self.suffix}", price=Decimal(price), stock=stock, **kwargs)
        product.set_current_language("sr")
        product.name = name
        product.slug = f"{slugify(name)}-{self.suffix}"
        product.save()
        return product

    def ids(self, response):
        self.assertEqual(response.status_code, 200)
        return [product.pk for product in response.context["products"]]

    def test_search_category_and_availability_are_intersected(self):
        response = self.client.get(self.url, {"q": "Tea", "kategorija": self.root.slug, "available": "1", "sort": "price_asc"})
        self.assertEqual(self.ids(response), [self.tea.pk, self.parent_tea.pk])
        self.assertNotIn(self.outside_tea.pk, self.ids(response))
        self.assertNotIn(self.archived.pk, self.ids(response))

    def test_search_uses_fallback_translation_sku_and_barcode(self):
        for query in ("Tea leaf", self.tea.sku, self.tea.barcode):
            with self.subTest(query=query):
                self.assertEqual(self.ids(self.client.get(self.url, {"q": query})), [self.tea.pk])

    def test_available_filter_excludes_zero_stock(self):
        response = self.client.get(self.url, {"kategorija": self.root.slug, "available": "1"})
        self.assertCountEqual(self.ids(response), [self.tea.pk, self.parent_tea.pk])

    def test_price_sort_uses_effective_price_and_ignores_invalid_discount(self):
        self.parent_tea.discount_price = Decimal("150")
        self.parent_tea.save()
        for sort, expected in (
            ("price_asc", [self.tea.pk, self.coffee.pk, self.parent_tea.pk]),
            ("price_desc", [self.parent_tea.pk, self.coffee.pk, self.tea.pk]),
        ):
            with self.subTest(sort=sort):
                response = self.client.get(self.url, {"kategorija": self.root.slug, "sort": sort})
                self.assertEqual(self.ids(response), expected)

    def test_invalid_sort_falls_back_to_default(self):
        response = self.client.get(self.url, {"sort": "price;DROP TABLE products"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["catalog_sort"], "default")

    def test_pagination_preserves_search_category_stock_sort_and_encoding(self):
        special = "Tea & milk"
        first = self.product(special + " A", self.child, price="20")
        second = self.product(special + " B", self.child, price="30")
        with patch.object(ProductListView, "paginate_by", 1):
            response = self.client.get(self.url, {"q": special, "kategorija": self.root.slug, "available": "1", "sort": "price_asc"})
            self.assertEqual(self.ids(response), [first.pk])
            href = re.search(r'rel="next" href="([^"]+)"', response.content.decode()).group(1)
            parsed = urlsplit(html.unescape(href))
            self.assertEqual(parse_qs(parsed.query), {"q": [special], "kategorija": [self.root.slug], "available": ["1"], "sort": ["price_asc"], "page": ["2"]})
            next_response = self.client.get(self.url + "?" + parsed.query)
            self.assertEqual(self.ids(next_response), [second.pk])

    def test_category_chips_keep_search_and_filters_but_reset_page(self):
        with patch.object(ProductListView, "paginate_by", 1):
            response = self.client.get(self.url, {"q": "Tea", "available": "1", "sort": "price_asc", "page": "2"})
        content = response.content.decode()
        nav = content.split('<nav class="category-nav', 1)[1].split("</nav>", 1)[0]
        links = [html.unescape(href) for href in re.findall(r'href="([^"]+)"', nav)]
        category_link = next(href for href in links if parse_qs(urlsplit(href).query).get("kategorija") == [self.root.slug])
        self.assertEqual(parse_qs(urlsplit(category_link).query), {"q": ["Tea"], "available": ["1"], "sort": ["price_asc"], "kategorija": [self.root.slug]})

    def test_empty_filtered_results_clear_to_real_path(self):
        response = self.client.get(self.url, {"q": "nothing-matches", "available": "1"})
        self.assertEqual(self.ids(response), [])
        self.assertContains(response, f'href="{self.url}?#catalog-results"')
        self.assertContains(response, "Clear filters")
        self.assertContains(response, "Browse all products")

    def test_empty_category_search_clear_preserves_category(self):
        response = self.client.get(self.url, {"q": "nothing-matches", "kategorija": self.root.slug})
        self.assertContains(response, f'href="{self.url}?kategorija={self.root.slug}#catalog-results"')

    def test_promo_and_recommended_controls_keep_listing_scope(self):
        self.parent_tea.is_recommended = True
        self.parent_tea.save()
        for route, expected in (("products:promo", self.tea), ("products:recommended", self.parent_tea)):
            with self.subTest(route=route):
                path = shop_reverse(route, language="en")
                response = self.client.get(path, {"q": "Tea", "available": "1", "sort": "price_asc"})
                self.assertEqual(self.ids(response), [expected.pk])
                self.assertContains(response, f'action="{path}#catalog-results"')

    def test_parent_category_lists_descendants_and_filters_them(self):
        path = shop_reverse("categories:detail", language="en", category_path=self.root.slug)
        response = self.client.get(path, {"q": "Tea", "available": "1", "sort": "price_asc"})
        self.assertEqual(self.ids(response), [self.tea.pk, self.parent_tea.pk])
        self.assertContains(response, "shop-category-subcategories")
        self.assertContains(response, f'action="{path}#catalog-results"')
        self.assertNotContains(response, "shop-category-grid")

    def test_out_of_stock_card_has_status_and_no_purchase_form(self):
        response = self.client.get(self.url, {"q": self.coffee.sku})
        self.assertContains(response, '<div class="shop-product-card__stock">')
        self.assertContains(response, "Out of stock")
        self.assertNotContains(response, f'id="qty-card-{self.coffee.pk}"')
        self.assertContains(response, self.coffee.get_absolute_url())

    def detail(self):
        return self.client.get(shop_reverse("products:detail", language="en", slug=self.tea.slug))

    def test_whitespace_descriptions_and_single_image_do_not_create_empty_sections(self):
        self.tea.short_description = "  "
        self.tea.description = " \n "
        self.tea.save()
        ProductImage.objects.create(product=self.tea, image="products/gallery/only.jpg")
        response = self.detail()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["gallery_image_count"], 1)
        self.assertNotContains(response, 'data-bs-target="#productGallery"')
        self.assertNotContains(response, 'class="shop-pdp__description"')
        self.assertNotContains(response, 'class="shop-pdp__lead"')

    def test_two_images_have_gallery_controls_and_attribution_is_preserved(self):
        self.tea.main_image = "products/main.jpg"
        self.tea.main_image_source_url = "https://example.com/original-product"
        self.tea.main_image_attribution = "Example manufacturer"
        self.tea.save()
        ProductImage.objects.create(product=self.tea, image="products/gallery/second.jpg")
        response = self.detail()
        self.assertEqual(response.context["gallery_image_count"], 2)
        self.assertContains(response, 'data-bs-target="#productGallery"')
        self.assertContains(response, "Example manufacturer")
        self.assertContains(response, self.tea.main_image_source_url)
