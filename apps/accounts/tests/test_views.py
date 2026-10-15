import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.auth.password_validation import MinimumLengthValidator
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import Client, RequestFactory, TestCase
from django.utils import translation

from apps.accounts.forms import LoginForm
from apps.accounts.models import CustomerProfile
from apps.accounts.views import UserLoginView, UserRegisterView
from apps.core.storefront_urls import shop_reverse

User = get_user_model()


def _apply_middleware(request) -> None:
    """Attach session and user to a bare RequestFactory request."""
    session_middleware = SessionMiddleware(lambda req: None)
    session_middleware.process_request(request)
    request.session.save()
    auth_middleware = AuthenticationMiddleware(lambda req: None)
    auth_middleware.process_request(request)
    message_middleware = MessageMiddleware(lambda req: None)
    message_middleware.process_request(request)


class AuthViewTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.factory = RequestFactory()

    def _get_view(self, view_class, path: str):
        request = self.factory.get(path)
        _apply_middleware(request)
        return view_class.as_view()(request)

    def test_register_page_loads(self) -> None:
        response = self._get_view(UserRegisterView, "/registracija/")
        self.assertEqual(response.status_code, 200)

    def test_login_page_loads(self) -> None:
        response = self._get_view(UserLoginView, "/prijava/")
        self.assertEqual(response.status_code, 200)

    def test_register_creates_user_and_profile(self) -> None:
        response = self.client.post(
            shop_reverse("accounts:register"),
            {
                "username": "novi_korisnik",
                "email": "novi@example.com",
                "first_name": "Novi",
                "last_name": "Korisnik",
                "phone": "+381601112233",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], shop_reverse("orders:history"))
        user = User.objects.get(username="novi_korisnik")
        self.assertEqual(user.email, "novi@example.com")
        profile = CustomerProfile.objects.get(user=user)
        self.assertEqual(profile.phone, "+381601112233")

    def test_register_logs_user_in(self) -> None:
        self.client.post(
            shop_reverse("accounts:register"),
            {
                "username": "logged_in",
                "email": "logged_in@example.com",
                "first_name": "Logged",
                "last_name": "In",
                "phone": "+381601112233",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )
        self.assertTrue(User.objects.filter(username="logged_in").exists())
        self.assertTrue(
            self.client.session.get("_auth_user_id"),
            "User should be logged in after registration.",
        )

    def test_login_success(self) -> None:
        User.objects.create_user(username="pera", password="SecurePass123!")
        response = self.client.post(
            shop_reverse("accounts:login"),
            {"username": "pera", "password": "SecurePass123!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], shop_reverse("orders:history"))

    def test_login_invalid(self) -> None:
        User.objects.create_user(username="pera", password="SecurePass123!")
        form = LoginForm(data={"username": "pera", "password": "wrong"})
        self.assertFalse(form.is_valid())

    def test_logout(self) -> None:
        User.objects.create_user(username="pera", password="SecurePass123!")
        self.client.login(username="pera", password="SecurePass123!")
        response = self.client.post(shop_reverse("accounts:logout"))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_register_requires_profile_fields(self) -> None:
        response = self.client.post(
            shop_reverse("accounts:register"),
            {
                "username": "incomplete",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="incomplete").exists())

    def test_register_requires_email(self) -> None:
        response = self.client.post(
            shop_reverse("accounts:register"),
            {
                "username": "no_email",
                "email": "",
                "first_name": "Test",
                "last_name": "User",
                "phone": "+381601112233",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="no_email").exists())
        self.assertContains(response, "id_email")

    def test_authenticated_user_redirected_from_register(self) -> None:
        User.objects.create_user(username="pera", password="SecurePass123!")
        self.client.login(username="pera", password="SecurePass123!")
        response = self.client.get(shop_reverse("accounts:register"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], shop_reverse("orders:history"))

class AccountLocaleTests(TestCase):
    def setUp(self):
        self.addCleanup(translation.deactivate)

    def main_content(self, response):
        self.assertEqual(response.status_code, 200)
        match = re.search(r"<main\b[^>]*>(.*?)</main>", response.content.decode(), re.S)
        self.assertIsNotNone(match)
        return match.group(1)

    def test_serbian_registration_labels_and_password_guidance_use_latin(self):
        response = self.client.get(shop_reverse("accounts:register", language="sr"))
        content = self.main_content(response)
        self.assertNotRegex(content, r"[\u0400-\u04ff]")
        self.assertIn("Potvrda lozinke", content)
        self.assertIn("Najviše 150 znakova", content)
        self.assertIn("najmanje 8 znakova", content)
        self.assertIn("ne sme biti previše slična", content)
        self.assertIn("ne sme biti često korišćena", content)
        self.assertIn("ne sme sadržati samo cifre", content)
        self.assertIn("Obavezna za potvrde narudžbina.", content)

    def test_registration_validation_errors_use_latin(self):
        base = {
            "username": "new-customer", "email": "new@example.com",
            "first_name": "Novi", "last_name": "Kupac", "phone": "+381601234567",
        }
        for passwords in (
            {"password1": "123", "password2": "123"},
            {"password1": "SecurePass123!", "password2": "DifferentPass123!"},
        ):
            with self.subTest(passwords=passwords):
                response = self.client.post(
                    shop_reverse("accounts:register", language="sr"),
                    {**base, **passwords},
                )
                self.assertNotRegex(self.main_content(response), r"[\u0400-\u04ff]")
                self.assertTrue(response.context["form"].errors)
                self.assertFalse(User.objects.filter(username=base["username"]).exists())

    def test_password_length_guidance_uses_serbian_latin_plural_forms(self):
        with translation.override("sr"):
            for length, ending in ((1, "1 znak."), (2, "2 znaka."), (8, "8 znakova.")):
                with self.subTest(length=length):
                    help_text = MinimumLengthValidator(min_length=length).get_help_text()
                    self.assertTrue(help_text.endswith(ending), help_text)
                    self.assertNotRegex(help_text, r"[\u0400-\u04ff]")

    def test_english_account_pages_use_english_headings_and_correct_email_help(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        for route, heading in (("accounts:login", "Sign in"), ("accounts:register", "Register")):
            with self.subTest(route=route):
                response = self.client.get(shop_reverse(route, language="en"))
                self.assertRegex(self.main_content(response), rf"<h1[^>]*>{heading}</h1>")
        self.assertContains(response, "Required for order confirmations.")
        self.assertNotContains(response, "Required for order confirmations and signing in.")
