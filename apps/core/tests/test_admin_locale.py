from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from apps.core.middleware import AdminSerbianLocaleMiddleware


class AdminSerbianLocaleMiddlewareTests(TestCase):
    def test_admin_path_uses_serbian(self) -> None:
        from django.http import HttpResponse

        factory = RequestFactory()
        request = factory.get("/admin/")
        request.LANGUAGE_CODE = "en"

        def get_response(req):
            return HttpResponse("ok")

        middleware = AdminSerbianLocaleMiddleware(get_response)
        middleware(request)
        self.assertEqual(request.LANGUAGE_CODE, "sr")

    def test_storefront_path_not_forced(self) -> None:
        from django.http import HttpResponse

        factory = RequestFactory()
        request = factory.get("/proizvodi/")
        request.LANGUAGE_CODE = "en"

        def get_response(req):
            return HttpResponse("ok")

        middleware = AdminSerbianLocaleMiddleware(get_response)
        middleware(request)
        self.assertEqual(request.LANGUAGE_CODE, "en")


class AdminBrandingTests(TestCase):
    def test_admin_index_uses_serbian_site_header(self) -> None:
        User = get_user_model()
        User.objects.create_superuser("admin", "admin@test.com", "pass")
        self.client.login(username="admin", password="pass")
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kod Pendule")
        self.assertContains(response, "ADMINISTRACIJA")
        self.assertContains(response, "Prihod danas")
        self.assertContains(response, "Pregled prodavnice")
        self.assertNotContains(response, "Choose a section below")

    def test_order_changelist_uses_accusative_narudzbinu(self) -> None:
        User = get_user_model()
        User.objects.create_superuser("admin", "admin@test.com", "pass")
        self.client.login(username="admin", password="pass")
        response = self.client.get(reverse("admin:orders_order_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1>Narudžbine</h1>")
        self.assertNotContains(response, "Izaberite Narudžbina za izmenu")

    def test_product_changelist_grammar_and_breadcrumb(self) -> None:
        User = get_user_model()
        User.objects.create_superuser("admin", "admin@test.com", "pass")
        self.client.login(username="admin", password="pass")
        response = self.client.get(reverse("admin:products_product_changelist"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("<h1>Proizvodi</h1>", html)
        self.assertIn("Dodaj proizvod", html)
        self.assertNotIn("Izaberite Proizvod", html)
        self.assertNotRegex(html, r"Proizvodi\s*›\s*Proizvodi")

    def test_category_changelist_grammar(self) -> None:
        User = get_user_model()
        User.objects.create_superuser("admin", "admin@test.com", "pass")
        self.client.login(username="admin", password="pass")
        response = self.client.get(reverse("admin:categories_category_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1>Kategorije</h1>")
        self.assertContains(response, "Dodaj kategoriju")

    def test_group_changelist_grammar(self) -> None:
        User = get_user_model()
        User.objects.create_superuser("admin", "admin@test.com", "pass")
        self.client.login(username="admin", password="pass")
        response = self.client.get(reverse("admin:auth_group_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Izaberite grupu za izmenu")
        self.assertContains(response, "Dodaj grupu")

    def test_admin_changelist_uses_latin_not_cyrillic(self) -> None:
        User = get_user_model()
        User.objects.create_superuser("admin", "admin@test.com", "pass")
        self.client.login(username="admin", password="pass")
        response = self.client.get(reverse("admin:auth_group_changelist"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Izaberite", html)
        self.assertIn("Pretraga", html)
        self.assertNotIn("Одабери", html)
        self.assertNotIn("ФИЛТЕР", html)
