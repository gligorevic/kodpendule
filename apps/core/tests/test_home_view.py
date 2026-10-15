import uuid
from decimal import Decimal

from django.test import TestCase

from apps.categories.models import Category
from apps.core.storefront_urls import shop_reverse
from apps.products.models import Product


class HomeFeaturedProductTests(TestCase):
    def test_featured_product_uses_recommended_not_newest(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        category = Category.objects.create(is_active=True)
        category.set_current_language("sr")
        category.name = "Pića"
        category.slug = f"pica-{suffix}"
        category.save()

        newest = Product.objects.create(
            category=category,
            sku=f"NEW-{suffix}",
            price=Decimal("100.00"),
            stock=5,
        )
        newest.set_current_language("sr")
        newest.name = "Rosa 1.5L"
        newest.slug = f"rosa-{suffix}"
        newest.save()

        recommended = Product.objects.create(
            category=category,
            sku=f"REC-{suffix}",
            price=Decimal("200.00"),
            stock=5,
            is_recommended=True,
            recommended_order=0,
        )
        recommended.set_current_language("sr")
        recommended.name = "Staff pick"
        recommended.slug = f"staff-{suffix}"
        recommended.save()

        response = self.client.get(shop_reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        featured = response.context["featured_product"]
        self.assertIsNone(featured)

    def test_featured_product_is_first_recommended_with_image(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        category = Category.objects.create(is_active=True)
        category.set_current_language("sr")
        category.name = "Pića"
        category.slug = f"pica2-{suffix}"
        category.save()

        from django.core.files.uploadedfile import SimpleUploadedFile

        image = SimpleUploadedFile(
            "pick.jpg",
            b"fake-image-bytes",
            content_type="image/jpeg",
        )
        recommended = Product.objects.create(
            category=category,
            sku=f"REC2-{suffix}",
            price=Decimal("200.00"),
            stock=5,
            is_recommended=True,
            recommended_order=0,
            main_image=image,
        )
        recommended.set_current_language("sr")
        recommended.name = "Staff pick with image"
        recommended.slug = f"staff2-{suffix}"
        recommended.save()

        response = self.client.get(shop_reverse("core:home"))
        featured = response.context["featured_product"]
        self.assertIsNotNone(featured)
        assert featured is not None
        self.assertEqual(featured.pk, recommended.pk)

    def test_homepage_shows_categories_after_hero(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        category = Category.objects.create(is_active=True, sort_order=0)
        category.set_current_language("sr")
        category.name = "Alkoholna pića"
        category.slug = f"alkoholna-pica-{suffix}"
        category.save()

        response = self.client.get(shop_reverse("core:home"))
        content = response.content.decode()
        hero_pos = content.find('class="shop-hero')
        categories_pos = content.find('id="home-categories"')
        trust_pos = content.find('class="shop-home-trust')
        self.assertGreater(categories_pos, hero_pos)
        self.assertGreater(trust_pos, categories_pos)
        self.assertContains(response, 'href="#home-categories"')
        self.assertContains(response, "Pogledaj ponudu")
        self.assertContains(response, "Alkoholna pića")


class HomeEverydaySelectionTests(TestCase):
    def setUp(self):
        self.suffix = uuid.uuid4().hex[:8]

    def category(self, name, **kwargs):
        category = Category.objects.create(is_active=True, **kwargs)
        category.set_current_language("sr")
        category.name = name
        category.slug = f"{name}-{self.suffix}"
        category.save()
        return category

    def product(self, category, name, **kwargs):
        values = {"price": Decimal("100"), "stock": 5, "main_image": "products/test-photo.jpg"}
        values.update(kwargs)
        product = Product.objects.create(category=category, sku=f"{name}-{self.suffix}", **values)
        product.set_current_language("sr")
        product.name = name
        product.slug = f"{name}-{self.suffix}"
        product.save()
        return product

    def selection(self):
        response = self.client.get(shop_reverse("core:home", language="sr"))
        self.assertEqual(response.status_code, 200)
        return response.context["everyday_products"]

    def test_everyday_selection_excludes_unavailable_archived_and_missing_photos(self):
        category = self.category("food")
        self.product(category, "sold-out", stock=0)
        self.product(category, "archived", is_archived=True)
        self.product(category, "no-photo", main_image="")
        eligible = self.product(category, "available-with-photo")

        self.assertEqual([product.pk for product in self.selection()], [eligible.pk])

    def test_everyday_selection_spans_departments_including_nested_categories(self):
        food = self.category("food", sort_order=2)
        drinks = self.category("drinks", sort_order=1)
        cleaning = self.category("cleaning", sort_order=0)
        waters = self.category("waters", parent=drinks)
        sparkling = self.category("sparkling", parent=waters)
        # If selection simply takes the first eight records, food crowds out
        # other departments. The deeper drinks category must still be represented.
        food_products = [self.product(food, f"food-{index}") for index in range(10)]
        water = self.product(sparkling, "sparkling-water")
        cleaner = self.product(cleaning, "cleaner")

        selected_ids = [product.pk for product in self.selection()]
        self.assertEqual(len(selected_ids), 8)
        self.assertEqual(len(set(selected_ids)), 8)
        self.assertIn(water.pk, selected_ids)
        self.assertIn(cleaner.pk, selected_ids)
        self.assertTrue(set(selected_ids) & {product.pk for product in food_products})
        self.assertEqual(
            selected_ids,
            [cleaner.pk, water.pk] + [product.pk for product in food_products[:6]],
        )

    def test_everyday_selection_is_empty_without_eligible_products(self):
        category = self.category("food")
        self.product(category, "unavailable", stock=0)
        self.product(category, "missing-photo", main_image="")
        self.assertEqual(self.selection(), [])
