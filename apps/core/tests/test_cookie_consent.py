"""Cookie consent banner and Google Maps."""

from django.conf import settings
from django.test import TestCase, override_settings

from apps.core.contact_details import DEFAULT_SHOP_EMAIL, DEFAULT_SHOP_PHONE
from apps.core.cookie_consent import (
    CONSENT_LEVEL_ALL,
    CONSENT_LEVEL_ESSENTIAL,
    parse_consent_cookie,
)
from apps.core.storefront_urls import shop_reverse


class CookieConsentParserTests(TestCase):
    def test_parse_valid_levels(self) -> None:
        self.assertEqual(parse_consent_cookie("v1:all"), CONSENT_LEVEL_ALL)
        self.assertEqual(parse_consent_cookie("v1:essential"), CONSENT_LEVEL_ESSENTIAL)
        self.assertEqual(parse_consent_cookie("v1%3Aall"), CONSENT_LEVEL_ALL)

    def test_parse_invalid(self) -> None:
        self.assertIsNone(parse_consent_cookie(""))
        self.assertIsNone(parse_consent_cookie("v2:all"))
        self.assertIsNone(parse_consent_cookie("invalid"))


class CookieBannerViewTests(TestCase):
    def test_banner_shown_without_consent_cookie(self) -> None:
        response = self.client.get(shop_reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "shop-cookie-banner")
        self.assertContains(response, "js-cookie-consent-accept")
        self.assertContains(response, "js-cookie-consent-decline")
        self.assertFalse(response.context["cookie_consent_given"])

    def test_banner_element_present_after_consent(self) -> None:
        self.client.cookies[settings.COOKIE_CONSENT_COOKIE_NAME] = "v1:essential"
        response = self.client.get(shop_reverse("core:home"))
        self.assertContains(response, 'id="shop-cookie-banner"')
        self.assertTrue(response.context["cookie_consent_given"])

    @override_settings(GOOGLE_MAPS_EMBED_URL="https://www.google.com/maps/embed?pb=test")
    def test_map_always_embedded_on_contact(self) -> None:
        response = self.client.get(shop_reverse("core:contact"))
        self.assertContains(response, "shop-map__iframe")
        self.assertNotContains(response, "shop-map--placeholder")
        self.assertNotContains(response, "data-shop-map-placeholder")

        self.client.cookies[settings.COOKIE_CONSENT_COOKIE_NAME] = "v1:essential"
        response = self.client.get(shop_reverse("core:contact"))
        self.assertContains(response, "shop-map__iframe")

    def test_footer_cookie_settings_link(self) -> None:
        self.client.cookies[settings.COOKIE_CONSENT_COOKIE_NAME] = "v1:essential"
        response = self.client.get(shop_reverse("core:home"))
        self.assertContains(response, "js-cookie-settings")


class ContactDetailsDefaultsTests(TestCase):
    def test_storefront_shows_default_phone_and_email(self) -> None:
        response = self.client.get(shop_reverse("core:contact"))
        self.assertContains(response, DEFAULT_SHOP_PHONE)
        self.assertContains(response, DEFAULT_SHOP_EMAIL)
        self.assertContains(response, f'tel:{DEFAULT_SHOP_PHONE.replace(" ", "")}')
        self.assertContains(response, f"mailto:{DEFAULT_SHOP_EMAIL}")
