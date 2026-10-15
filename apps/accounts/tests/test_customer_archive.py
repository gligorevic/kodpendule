from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import CustomerContact, CustomerProfile
from apps.accounts.services import archive_customer_from_checkout, archive_customer_from_registration
from apps.accounts.services.customer_archive import normalize_customer_email
from apps.cart.cart import get_cart
from apps.checkout.tests.test_checkout import CheckoutServiceTests
from apps.core.storefront_urls import shop_reverse
from apps.orders.services import create_order_from_checkout
from apps.orders.models import PaymentMethod

User = get_user_model()


class CustomerArchiveServiceTests(TestCase):
    def test_normalize_email_lowercases(self) -> None:
        self.assertEqual(normalize_customer_email("  User@Example.COM "), "user@example.com")

    def test_checkout_then_register_same_email_single_row(self) -> None:
        archive_customer_from_checkout(
            email="buyer@example.com",
            first_name="Guest",
            last_name="Buyer",
            phone="+381601112233",
        )
        user = User.objects.create_user(
            username="buyer",
            email="Buyer@example.com",
            first_name="Registered",
            last_name="Buyer",
            password="SecurePass123!",
        )
        CustomerProfile.objects.create(user=user, phone="+381609998877")
        archive_customer_from_registration(user)

        contacts = CustomerContact.objects.filter(email="buyer@example.com")
        self.assertEqual(contacts.count(), 1)
        contact = contacts.get()
        self.assertEqual(contact.user_id, user.pk)
        self.assertEqual(contact.first_name, "Registered")
        self.assertEqual(contact.phone, "+381609998877")
        self.assertEqual(contact.order_count, 1)
        self.assertIsNotNone(contact.registered_at)

    def test_register_then_checkout_same_email_single_row(self) -> None:
        user = User.objects.create_user(
            username="member",
            email="member@example.com",
            first_name="Member",
            last_name="Shopper",
            password="SecurePass123!",
        )
        CustomerProfile.objects.create(user=user, phone="+381601112233")
        archive_customer_from_registration(user)

        archive_customer_from_checkout(
            email="member@example.com",
            first_name="Member",
            last_name="Shopper",
            phone="+381601112233",
            user=user,
        )

        self.assertEqual(CustomerContact.objects.count(), 1)
        contact = CustomerContact.objects.get()
        self.assertEqual(contact.order_count, 1)
        self.assertEqual(contact.user_id, user.pk)


class CustomerArchiveCheckoutIntegrationTests(CheckoutServiceTests):
    def test_create_order_archives_guest_contact(self) -> None:
        cart = get_cart(self.request)
        order = create_order_from_checkout(
            cart=cart,
            user=None,
            guest_email="guest@example.com",
            first_name="Ana",
            last_name="Anic",
            phone="+381601112233",
            shipping_city=self.city,
            shipping_street="Ulica 1",
            order_notes="Ring the bell",
            payment_method=PaymentMethod.CASH,
        )
        self.assertIsNotNone(order.pk)
        contact = CustomerContact.objects.get(email="guest@example.com")
        self.assertEqual(contact.first_name, "Ana")
        self.assertEqual(contact.order_count, 1)
        self.assertEqual(contact.delivery_street, "Ulica 1")
        self.assertEqual(contact.delivery_city_name, self.city.name)
        self.assertIsNone(contact.user_id)


class CustomerArchiveRegistrationTests(TestCase):
    def setUp(self) -> None:
        from django.test import Client

        self.client = Client()

    def test_register_creates_customer_contact(self) -> None:
        response = self.client.post(
            shop_reverse("accounts:register"),
            {
                "username": "archived",
                "email": "archived@example.com",
                "first_name": "Ar",
                "last_name": "Hiv",
                "phone": "+381601112233",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )
        self.assertEqual(response.status_code, 302)
        contact = CustomerContact.objects.get(email="archived@example.com")
        self.assertEqual(contact.first_name, "Ar")
        self.assertEqual(contact.phone, "+381601112233")
        self.assertIsNotNone(contact.registered_at)
        self.assertEqual(contact.order_count, 0)
