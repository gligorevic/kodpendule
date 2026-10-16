from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import CustomerContact

User = get_user_model()


class ShopUserAdminTests(TestCase):
    def setUp(self) -> None:
        self.admin = User.objects.create_superuser("admin", "admin@test.com", "pass")
        self.client = Client()
        self.client.force_login(self.admin)

        self.shop_user = User.objects.create_user(
            username="pera",
            email="pera@example.com",
            password="SecurePass123!",
            first_name="Pera",
            last_name="Perić",
        )
        CustomerContact.objects.create(
            email="pera@example.com",
            user=self.shop_user,
            first_name="Pera",
            last_name="Perić",
        )

        User.objects.create_superuser("staff", "staff@test.com", "pass")

    def test_changelist_shows_registered_shop_users_only(self) -> None:
        response = self.client.get(reverse("admin:accounts_user_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "pera@example.com")
        self.assertNotContains(response, "staff@test.com")

    def test_changelist_uses_serbian_title(self) -> None:
        response = self.client.get(reverse("admin:accounts_user_changelist"))
        self.assertContains(response, "<h1>Korisnici</h1>")
