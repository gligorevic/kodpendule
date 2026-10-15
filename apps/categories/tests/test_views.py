import uuid
from decimal import Decimal

from django.http import Http404
from django.test import RequestFactory, TestCase
from django.utils import translation

from apps.categories.models import Category
from apps.categories.selectors import (
    category_path_for_url,
    get_category_by_path,
    get_category_by_slug,
)
from apps.categories.views import CategoryDetailView, CategoryListView
from apps.core.tests.test_utils import apply_request_middleware
from apps.products.models import Product


class CategoryViewTests(TestCase):
    def tearDown(self) -> None:
        translation.deactivate()

    def setUp(self) -> None:
        self.factory = RequestFactory()
        suffix = uuid.uuid4().hex[:8]
        self.category_slug = f"satovi-{suffix}"

        self.category = Category.objects.create(is_active=True)
        self.category.set_current_language("sr")
        self.category.name = "Satovi"
        self.category.slug = self.category_slug
        self.category.description = "Svi satovi."
        self.category.save()

        self.product = Product.objects.create(
            category=self.category,
            sku=f"SKU-{suffix}",
            price=Decimal("1500.00"),
            stock=5,
        )
        self.product.set_current_language("sr")
        self.product.name = "Klasični sat"
        self.product.slug = f"klasicni-sat-{suffix}"
        self.product.save()

    def _get(self, view_class, path: str, **kwargs):
        request = self.factory.get(path)
        apply_request_middleware(request)
        return view_class.as_view()(request, **kwargs)

    def test_category_list_returns_200(self) -> None:
        response = self._get(CategoryListView, "/kategorije/")
        self.assertEqual(response.status_code, 200)

    def test_category_list_shows_root_categories_only(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        child = Category.objects.create(is_active=True, parent=self.category)
        child.set_current_language("sr")
        child.name = "Podkategorija"
        child.slug = f"pod-{suffix}"
        child.save()

        response = self._get(CategoryListView, "/kategorije/")
        self.assertEqual(response.status_code, 200)
        response.render()
        content = response.content.decode()
        self.assertIn("shop-category-grid", content)
        self.assertIn("Satovi", content)
        self.assertNotIn("Podkategorija", content)
        self.assertEqual(content.count('class="shop-category-card"'), 1)

    def test_category_detail_shows_subcategory_links_and_products(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        child = Category.objects.create(is_active=True, parent=self.category)
        child.set_current_language("sr")
        child.name = "Podkategorija"
        child.slug = f"pod-{suffix}"
        child.save()

        response = self._get(
            CategoryDetailView,
            f"/kategorije/{self.category_slug}/",
            category_path=self.category_slug,
        )
        self.assertEqual(response.status_code, 200)
        response.render()
        content = response.content.decode()
        self.assertIn("shop-category-subcategories", content)
        self.assertIn("Podkategorija", content)
        self.assertIn("Klasični sat", content)

    def test_category_detail_shows_products_on_leaf_category(self) -> None:
        response = self._get(
            CategoryDetailView,
            f"/kategorije/{self.category_slug}/",
            category_path=self.category_slug,
        )
        self.assertEqual(response.status_code, 200)
        response.render()
        content = response.content.decode()
        self.assertIn("Klasični sat", content)
        self.assertNotIn("shop-category-grid", content)

    def test_category_detail_404(self) -> None:
        with self.assertRaises(Http404):
            self._get(
                CategoryDetailView,
                "/kategorije/nema/",
                category_path="nema",
            )

    def test_nested_category_requires_hierarchical_path(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        root_slug = f"srpski-{suffix}"
        child_slug = f"sub1-{suffix}"
        leaf_slug = f"subsub1-{suffix}"

        root = Category.objects.create(is_active=True)
        root.set_current_language("sr")
        root.name = "Srpski"
        root.slug = root_slug
        root.save()

        child = Category.objects.create(is_active=True, parent=root)
        child.set_current_language("sr")
        child.name = "Sub1"
        child.slug = child_slug
        child.save()

        leaf = Category.objects.create(is_active=True, parent=child)
        leaf.set_current_language("sr")
        leaf.name = "Subsub1"
        leaf.slug = leaf_slug
        leaf.save()

        hierarchical = f"{root_slug}/{child_slug}/{leaf_slug}"
        self.assertEqual(
            category_path_for_url(leaf, "sr"),
            hierarchical,
        )
        self.assertIsNotNone(get_category_by_path(hierarchical, "sr"))

        flat_response = self._get(
            CategoryDetailView,
            f"/kategorije/{leaf_slug}/",
            category_path=leaf_slug,
        )
        self.assertEqual(flat_response.status_code, 301)
        self.assertEqual(
            flat_response["Location"],
            f"/kategorije/{hierarchical}/",
        )

        response = self._get(
            CategoryDetailView,
            f"/kategorije/{hierarchical}/",
            category_path=hierarchical,
        )
        self.assertEqual(response.status_code, 200)

    def test_flat_nested_url_redirects_to_hierarchical_path(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        root_slug = f"root-{suffix}"
        leaf_slug = f"leaf-{suffix}"

        root = Category.objects.create(is_active=True)
        root.set_current_language("sr")
        root.name = "Root"
        root.slug = root_slug
        root.save()

        leaf = Category.objects.create(is_active=True, parent=root)
        leaf.set_current_language("sr")
        leaf.name = "Leaf"
        leaf.slug = leaf_slug
        leaf.save()

        response = self._get(
            CategoryDetailView,
            f"/kategorije/{leaf_slug}/",
            category_path=leaf_slug,
        )
        self.assertEqual(response.status_code, 301)
        self.assertEqual(
            response["Location"],
            f"/kategorije/{root_slug}/{leaf_slug}/",
        )

    def test_get_category_by_slug(self) -> None:
        category = get_category_by_slug(self.category_slug, "sr")
        self.assertIsNotNone(category)
        self.assertEqual(category.name, "Satovi")
