from django.test import TestCase, override_settings

from apps.core.contact_details import DEFAULT_SHOP_EMAIL, DEFAULT_SHOP_PHONE, resolve_contact_details
from apps.core.models import FooterSettings
from apps.core.storefront_urls import shop_reverse


class ContactDetailsTests(TestCase):
    def test_defaults_when_footer_empty(self) -> None:
        details = resolve_contact_details(None)
        self.assertEqual(details.phone, DEFAULT_SHOP_PHONE)
        self.assertEqual(details.email, DEFAULT_SHOP_EMAIL)

    def test_footer_overrides_defaults(self) -> None:
        footer = FooterSettings(pk=1)
        footer.set_current_language("sr")
        footer.phone = "+381 64 999 8888"
        footer.email = "prodavnica@example.com"
        footer.address = "Test adresa"
        footer.save()
        details = resolve_contact_details(footer)
        self.assertEqual(details.phone, "+381 64 999 8888")
        self.assertEqual(details.email, "prodavnica@example.com")


class ContactPageTests(TestCase):
    @override_settings(GOOGLE_MAPS_EMBED_URL="https://www.google.com/maps/embed?pb=test")
    def test_contact_page_renders_details_and_map(self) -> None:
        response = self.client.get(shop_reverse("core:contact"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, DEFAULT_SHOP_PHONE)
        self.assertContains(response, DEFAULT_SHOP_EMAIL)
        self.assertContains(response, "shop-map")
