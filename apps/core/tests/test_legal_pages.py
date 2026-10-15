"""Legal pages and checkout consent tests."""

from __future__ import annotations

from django.test import TestCase, override_settings

from apps.checkout.forms import CheckoutForm
from apps.core.storefront_urls import shop_reverse
from apps.shipping.models import City


class LegalPageViewTests(TestCase):
    def test_terms_page_sr(self) -> None:
        response = self.client.get(shop_reverse("core:terms"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, shop_reverse("core:privacy"))

    def test_privacy_page_sr(self) -> None:
        response = self.client.get(shop_reverse("core:privacy"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, shop_reverse("core:terms"))

    def test_footer_contains_legal_links(self) -> None:
        response = self.client.get(shop_reverse("core:home"))
        self.assertContains(response, shop_reverse("core:terms"))
        self.assertContains(response, shop_reverse("core:privacy"))

    def test_header_nav_contains_legal_links(self) -> None:
        response = self.client.get(shop_reverse("core:home"))
        self.assertContains(response, 'aria-label="Glavna navigacija"')
        self.assertContains(response, shop_reverse("core:terms"))
        self.assertContains(response, shop_reverse("core:privacy"))

    @override_settings(GOOGLE_MAPS_EMBED_URL="https://www.google.com/maps/embed?pb=test")
    def test_contact_page_includes_map(self) -> None:
        response = self.client.get(shop_reverse("core:contact"))
        self.assertContains(response, 'class="shop-map__iframe"')
        self.assertContains(response, "loading=\"lazy\"")


class CheckoutLegalConsentTests(TestCase):
    def setUp(self) -> None:
        from apps.cart.cart import SESSION_KEY
        from apps.categories.models import Category
        from apps.products.models import Product

        self.city = City.objects.create(
            name="Beograd",
            slug="bg-legal",
            shipping_price=350,
            is_active=True,
        )
        category = Category.objects.create(is_active=True)
        category.set_current_language("sr")
        category.name = "Kat"
        category.slug = "kat-legal"
        category.save()
        product = Product.objects.create(
            category=category,
            sku="SKU-LEGAL",
            price=500,
            stock=5,
        )
        product.set_current_language("sr")
        product.name = "Legal test product"
        product.slug = "legal-test"
        product.save()
        session = self.client.session
        session[SESSION_KEY] = {str(product.pk): 1}
        session.save()

    def _valid_data(self, **overrides):
        data = {
            "guest_email": "guest@example.com",
            "first_name": "Ana",
            "last_name": "Anić",
            "phone": "0601234567",
            "shipping_city": self.city.pk,
            "shipping_street": "Ulica 1",
            "order_notes": "",
            "accept_legal": True,
        }
        data.update(overrides)
        return data

    def test_checkout_requires_legal_consent(self) -> None:
        form = CheckoutForm(data=self._valid_data(accept_legal=False), user=None)
        self.assertFalse(form.is_valid())
        self.assertIn("accept_legal", form.errors)

    def test_checkout_page_shows_consent_checkbox(self) -> None:
        response = self.client.get(shop_reverse("checkout:checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="accept_legal"')
        self.assertContains(response, shop_reverse("core:terms"))
        self.assertContains(response, shop_reverse("core:privacy"))
