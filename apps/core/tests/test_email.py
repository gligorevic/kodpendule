"""Email delivery tests (locmem backend)."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.core.mail import send_shop_email
from apps.core.services.contact_email import send_contact_form_email
from apps.orders.models import Order, OrderItem, OrderStatus, PaymentMethod
from apps.shipping.models import City
from apps.orders.services.order_notifications import (
    notify_customer_new_order,
    notify_staff_new_order,
)
from apps.products.models import Product
from apps.products.services.stock_notifications import notify_low_stock_if_crossed_threshold

EMAIL_SETTINGS = {
    "EMAIL_BACKEND": "django.core.mail.backends.locmem.EmailBackend",
    "EMAIL_HOST": "smtp.sendgrid.net",
    "SENDGRID_API_KEY": "test-key",
    "SHOP_FROM_EMAIL": "info@kodpendule.com",
    "SHOP_NOTIFICATION_EMAIL": "kodpendule@gmail.com",
    "DEFAULT_FROM_EMAIL": "info@kodpendule.com",
}


@override_settings(**EMAIL_SETTINGS)
class SendShopEmailTests(TestCase):
    def test_send_shop_email_delivers(self) -> None:
        ok = send_shop_email(
            subject="Test",
            message="Body",
            recipient_list=["user@example.com"],
        )
        self.assertTrue(ok)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["user@example.com"])
        self.assertIn("info@kodpendule.com", mail.outbox[0].from_email)
        self.assertIn("Kod Pendule", mail.outbox[0].from_email)

    def test_staff_notifications_go_to_shop_inbox_not_from_address(self) -> None:
        ok = send_shop_email(
            subject="Staff alert",
            message="Body",
            recipient_list=["kodpendule@gmail.com"],
        )
        self.assertTrue(ok)
        self.assertEqual(mail.outbox[-1].to, ["kodpendule@gmail.com"])
        self.assertIn("info@kodpendule.com", mail.outbox[-1].from_email)

    @override_settings(SENDGRID_API_KEY="", EMAIL_HOST="")
    def test_skips_when_not_configured(self) -> None:
        ok = send_shop_email(
            subject="Test",
            message="Body",
            recipient_list=["user@example.com"],
        )
        self.assertFalse(ok)
        self.assertEqual(len(mail.outbox), 0)

    def test_backend_returning_zero_is_not_reported_as_success(self):
        with patch("apps.core.mail.EmailMessage.send", return_value=0):
            self.assertFalse(send_shop_email(subject="Test", message="Body", recipient_list=["user@example.com"]))

    def test_failure_does_not_raise(self) -> None:
        with patch(
            "apps.core.mail.EmailMessage.send",
            side_effect=ConnectionError("SMTP down"),
        ):
            ok = send_shop_email(
                subject="Test",
                message="Body",
                recipient_list=["user@example.com"],
            )
        self.assertFalse(ok)


@override_settings(**EMAIL_SETTINGS)
class ContactEmailTests(TestCase):
    def test_contact_form_email(self) -> None:
        ok = send_contact_form_email(
            name="Ana",
            email="ana@example.com",
            phone="+381601112233",
            message="Pitanje o dostavi.",
        )
        self.assertTrue(ok)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["kodpendule@gmail.com"])
        self.assertEqual(mail.outbox[0].reply_to, ["ana@example.com"])
        self.assertIn("info@kodpendule.com", mail.outbox[0].from_email)
        self.assertIn("Ana", mail.outbox[0].body)


@override_settings(**EMAIL_SETTINGS)
class OrderEmailTests(TestCase):
    def setUp(self) -> None:
        city = City.objects.create(
            name="Beograd",
            slug="beograd-email-test",
            shipping_price=Decimal("350.00"),
            is_active=True,
        )
        self.order = Order.objects.create(
            order_number="KP-20260101-ABC123",
            guest_email="customer@example.com",
            first_name="Pera",
            last_name="Perić",
            phone="+381601112233",
            shipping_street="Ulica 1",
            shipping_city=city,
            shipping_city_name="Beograd",
            requested_delivery_date=timezone.localdate(),
            shipping_price=Decimal("350.00"),
            payment_method=PaymentMethod.CASH,
            status=OrderStatus.PENDING,
            subtotal=Decimal("2000.00"),
            total=Decimal("2350.00"),
        )
        OrderItem.objects.create(
            order=self.order,
            product_name="Test product",
            sku="SKU-1",
            unit_price=Decimal("2000.00"),
            quantity=1,
        )

    def test_customer_order_email(self) -> None:
        notify_customer_new_order(self.order)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["customer@example.com"])
        self.assertIn("KP-20260101-ABC123", mail.outbox[0].subject)
        self.assertIn("Test product", mail.outbox[0].body)
        self.assertIn("2 350,00 din", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].reply_to, ["kodpendule@gmail.com"])

    def test_staff_order_email(self) -> None:
        notify_staff_new_order(self.order)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["kodpendule@gmail.com"])
        self.assertIn("KP-20260101-ABC123", mail.outbox[0].subject)
        self.assertIn(str(self.order.get_payment_method_display()), mail.outbox[0].body)


@override_settings(**EMAIL_SETTINGS)
class LowStockEmailTests(TestCase):
    def setUp(self) -> None:
        from apps.categories.models import Category

        category = Category.objects.create(is_active=True)
        category.set_current_language("sr")
        category.name = "Kat"
        category.slug = "kat-stock"
        category.save()

        self.product = Product.objects.create(
            category=category,
            sku="SKU-LOW",
            price=Decimal("100.00"),
            stock=6,
            minimum_stock_alert=5,
        )
        self.product.set_current_language("sr")
        self.product.name = "Low stock item"
        self.product.slug = "low-stock"
        self.product.save()

    def test_low_stock_email_on_threshold_cross(self) -> None:
        self.product.stock = 5
        self.product.save(update_fields=["stock"])
        notify_low_stock_if_crossed_threshold(product=self.product, stock_before=6)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Low stock", mail.outbox[0].subject)
        self.assertIn("SKU-LOW", mail.outbox[0].body)

    def test_no_email_when_already_below_threshold(self) -> None:
        self.product.stock = 4
        self.product.save(update_fields=["stock"])
        notify_low_stock_if_crossed_threshold(product=self.product, stock_before=5)
        self.assertEqual(len(mail.outbox), 0)
