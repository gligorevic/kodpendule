import uuid
from decimal import Decimal

from django.conf import settings
from django.core import mail
from django.db import connection
from django.test import Client, RequestFactory, TestCase, override_settings
from django.test.utils import CaptureQueriesContext

from apps.cart.cart import SESSION_KEY, get_cart
from apps.categories.models import Category
from apps.checkout.forms import CheckoutForm
from apps.core.checkout_settings import (
    DeliveryTiming,
    ThresholdShippingMode,
    checkout_today,
    min_scheduled_delivery_date,
    resolve_checkout_shipping_price,
)
from apps.core.storefront_urls import shop_reverse
from apps.orders.models import Order, PaymentMethod
from apps.orders.services import create_order_from_checkout
from apps.orders.services.order_service import CheckoutError
from apps.products.models import Product
from apps.shipping.models import City


def _checkout_post_data(city_pk: int, **overrides) -> dict[str, str]:
    data = {
        "guest_email": "guest@example.com",
        "first_name": "Pera",
        "last_name": "Perić",
        "phone": "+381601112233",
        "shipping_city": str(city_pk),
        "shipping_street": "Ulica 1",
        "delivery_timing": DeliveryTiming.SAME_DAY,
        "order_notes": "",
        "payment_method": PaymentMethod.CASH,
        "accept_legal": "on",
    }
    data.update(overrides)
    return data


class CheckoutServiceTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.session = self.client.session

        self.city = City.objects.create(
            name="Beograd",
            slug="beograd",
            shipping_price=Decimal("350.00"),
            is_active=True,
        )

        suffix = uuid.uuid4().hex[:8]
        category = Category.objects.create(is_active=True)
        category.set_current_language("sr")
        category.name = "Kat"
        category.slug = f"kat-{suffix}"
        category.save()

        self.product = Product.objects.create(
            category=category,
            sku=f"SKU-CHK-{suffix}",
            price=Decimal("2000.00"),
            stock=10,
        )
        self.product.set_current_language("sr")
        self.product.name = "Checkout product"
        self.product.slug = f"chk-{suffix}"
        self.product.save()

        cart = get_cart(self.request)
        cart.add(self.product, 1)

    def test_create_order_from_checkout(self) -> None:
        cart = get_cart(self.request)
        order = create_order_from_checkout(
            cart=cart,
            user=None,
            guest_email="guest@example.com",
            first_name="Pera",
            last_name="Perić",
            phone="+381601112233",
            shipping_city=self.city,
            shipping_street="Ulica 1",
            order_notes="Pozvati pre dostave.",
            payment_method=PaymentMethod.CASH,
        )
        self.assertRegex(order.order_number, r"^KP-\d{6}$")
        self.assertTrue(order.is_new)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.total, Decimal("2350.00"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 9)
        self.assertTrue(get_cart(self.request).is_empty)

    def test_free_shipping_when_threshold_met(self) -> None:
        self.city.promo_cart_threshold = Decimal("1000.00")
        self.city.promo_shipping_mode = ThresholdShippingMode.FREE
        self.city.save()

        price = resolve_checkout_shipping_price(
            subtotal=Decimal("2000.00"),
            city=self.city,
            requested_delivery_date=checkout_today(),
        )
        self.assertEqual(price, Decimal("0"))

    def test_product_archived_after_adding_to_cart_cannot_be_purchased(self) -> None:
        Product.objects.filter(pk=self.product.pk).update(is_archived=True)
        with self.assertRaises(CheckoutError):
            create_order_from_checkout(
                cart=get_cart(self.request), user=None, guest_email="guest@example.com",
                first_name="Pera", last_name="Perić", phone="+381601112233",
                shipping_city=self.city, shipping_street="Ulica 1",
                order_notes="", payment_method=PaymentMethod.CASH,
            )
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)
        self.assertFalse(Order.objects.exists())

    def test_multiple_products_lock_by_pk_and_keep_cart_item_order(self) -> None:
        second = Product.objects.create(
            category=self.product.category, sku="SECOND-LOCK-TEST",
            price=Decimal("50.00"), stock=6,
        )
        cart = get_cart(self.request)
        cart.clear()
        cart.add(second, 2)
        cart.add(self.product, 1)
        with CaptureQueriesContext(connection) as queries:
            order = create_order_from_checkout(
                cart=cart, user=None, guest_email="guest@example.com",
                first_name="Pera", last_name="Perić", phone="+381601112233",
                shipping_city=self.city, shipping_street="Ulica 1",
                order_notes="", payment_method=PaymentMethod.CASH,
            )
        product_lock_queries = [
            query["sql"] for query in queries
            if 'ORDER BY "products_product"."id" ASC' in query["sql"]
        ]
        self.assertEqual(len(product_lock_queries), 1)
        self.assertEqual(list(order.items.order_by("pk").values_list("product_id", flat=True)), [second.pk, self.product.pk])
        second.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual((second.stock, self.product.stock), (4, 9))

    def test_scheduled_delivery_is_free_even_below_promo_threshold(self) -> None:
        future_date = min_scheduled_delivery_date()
        price = resolve_checkout_shipping_price(
            subtotal=Decimal("100.00"),
            city=self.city,
            requested_delivery_date=future_date,
        )
        self.assertEqual(price, Decimal("0"))

    def test_discounted_shipping_when_threshold_met(self) -> None:
        self.city.promo_cart_threshold = Decimal("1000.00")
        self.city.promo_shipping_mode = ThresholdShippingMode.DISCOUNTED
        self.city.promo_discounted_shipping_price = Decimal("199.00")
        self.city.save()

        price = resolve_checkout_shipping_price(
            subtotal=Decimal("2000.00"),
            city=self.city,
            requested_delivery_date=checkout_today(),
        )
        self.assertEqual(price, Decimal("199.00"))

    def test_checkout_form_allows_empty_notes(self) -> None:
        form = CheckoutForm(
            data={
                "guest_email": "a@b.rs",
                "first_name": "A",
                "last_name": "B",
                "phone": "123",
                "shipping_city": self.city.pk,
                "shipping_street": "St",
                "delivery_timing": DeliveryTiming.SAME_DAY,
                "order_notes": "",
                "payment_method": PaymentMethod.CARD,
                "accept_legal": True,
            },
            user=None,
        )
        self.assertTrue(form.is_valid())

    def test_checkout_form_requires_payment_method(self) -> None:
        form = CheckoutForm(
            data={
                "guest_email": "a@b.rs",
                "first_name": "A",
                "last_name": "B",
                "phone": "123",
                "shipping_city": self.city.pk,
                "shipping_street": "St",
                "delivery_timing": DeliveryTiming.SAME_DAY,
                "order_notes": "",
                "accept_legal": True,
            },
            user=None,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("payment_method", form.errors)

    def test_checkout_form_requires_date_for_scheduled_delivery(self) -> None:
        form = CheckoutForm(
            data={
                "guest_email": "a@b.rs",
                "first_name": "A",
                "last_name": "B",
                "phone": "123",
                "shipping_city": self.city.pk,
                "shipping_street": "St",
                "delivery_timing": DeliveryTiming.SCHEDULED,
                "order_notes": "",
                "payment_method": PaymentMethod.CASH,
                "accept_legal": True,
            },
            user=None,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("requested_delivery_date", form.errors)

    def test_checkout_form_rejects_today_for_scheduled_delivery(self) -> None:
        form = CheckoutForm(
            data={
                "guest_email": "a@b.rs",
                "first_name": "A",
                "last_name": "B",
                "phone": "123",
                "shipping_city": self.city.pk,
                "shipping_street": "St",
                "delivery_timing": DeliveryTiming.SCHEDULED,
                "requested_delivery_date": checkout_today().isoformat(),
                "order_notes": "",
                "payment_method": PaymentMethod.CASH,
                "accept_legal": True,
            },
            user=None,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("requested_delivery_date", form.errors)

    def test_required_field_errors_use_latin_not_cyrillic(self) -> None:
        form = CheckoutForm(
            data={
                "guest_email": "",
                "first_name": "",
                "last_name": "",
                "phone": "",
                "shipping_city": "",
                "shipping_street": "",
                "delivery_timing": DeliveryTiming.SAME_DAY,
                "order_notes": "",
            },
            user=None,
        )
        self.assertFalse(form.is_valid())
        errors_text = " ".join(str(error) for errors in form.errors.values() for error in errors)
        self.assertIn("Ovo polje je obavezno", errors_text)
        self.assertNotIn("Ово", errors_text)

    def test_checkout_page_omits_removed_fields(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        category = Category.objects.create(is_active=True)
        category.set_current_language("sr")
        category.name = "Kat"
        category.slug = f"kat-ui-{suffix}"
        category.save()
        product = Product.objects.create(
            category=category,
            sku=f"SKU-UI-{suffix}",
            price=Decimal("500.00"),
            stock=2,
        )
        session = self.client.session
        session[SESSION_KEY] = {str(product.pk): 1}
        session.save()

        response = self.client.get(shop_reverse("checkout:checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "id_shipping_postal_code")
        self.assertNotContains(response, "id_delivery_date")
        self.assertNotContains(response, "id_flexible_delivery")
        self.assertNotContains(response, "Shipping method")
        self.assertContains(response, "id_requested_delivery_date")


class CheckoutViewTests(TestCase):
    def setUp(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        self.vrdnik = City.objects.create(
            name="Vrdnik",
            slug=f"vrdnik-{suffix}",
            shipping_price=Decimal("450.00"),
            is_active=True,
        )
        category = Category.objects.create(is_active=True)
        category.set_current_language("sr")
        category.name = "Kat"
        category.slug = f"kat-{suffix}"
        category.save()

        self.product = Product.objects.create(
            category=category,
            sku=f"SKU-CHK2-{suffix}",
            price=Decimal("1000.00"),
            stock=10,
        )
        self.product.set_current_language("sr")
        self.product.name = "Product"
        self.product.slug = f"prod-{suffix}"
        self.product.save()

        session = self.client.session
        session[SESSION_KEY] = {str(self.product.pk): 1}
        session.save()

    def test_checkout_page_includes_shipping_scripts(self) -> None:
        response = self.client.get(shop_reverse("checkout:checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="city-delivery-data"')
        self.assertContains(response, 'id="checkout-today-data"')
        self.assertContains(response, "delivery_timing")
        self.assertNotContains(response, 'id="checkout-shipping-rules"')
        self.assertContains(response, f'"{self.vrdnik.pk}"')

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_HOST="smtp.sendgrid.net",
        SENDGRID_API_KEY="test-key",
        SHOP_NOTIFICATION_EMAIL="shop@example.com",
    )
    def test_checkout_triggers_low_stock_email(self) -> None:
        self.product.minimum_stock_alert = 10
        self.product.stock = 11
        self.product.save(update_fields=["minimum_stock_alert", "stock"])
        mail.outbox.clear()

        response = self.client.post(
            shop_reverse("checkout:checkout"),
            _checkout_post_data(self.vrdnik.pk),
        )
        self.assertEqual(response.status_code, 302)
        low_stock_msgs = [m for m in mail.outbox if "Malo zaliha" in m.subject or "Low stock" in m.subject]
        self.assertEqual(len(low_stock_msgs), 1)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_HOST="smtp.sendgrid.net",
        SENDGRID_API_KEY="test-key",
        SHOP_NOTIFICATION_EMAIL="shop@example.com",
    )
    def test_post_checkout_sends_customer_and_staff_emails(self) -> None:
        mail.outbox.clear()
        response = self.client.post(
            shop_reverse("checkout:checkout"),
            _checkout_post_data(self.vrdnik.pk),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 2)
        recipients = {addr for msg in mail.outbox for addr in msg.to}
        self.assertEqual(recipients, {"guest@example.com", "shop@example.com"})

    def test_checkout_rejects_order_without_legal_consent(self) -> None:
        post_data = _checkout_post_data(self.vrdnik.pk)
        post_data.pop("accept_legal")
        response = self.client.post(
            shop_reverse("checkout:checkout"),
            post_data,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        self.assertContains(response, "accept_legal")

    def test_post_checkout_places_order_clears_cart_and_redirects(self) -> None:
        with self.settings(SHOP_NOTIFICATION_EMAIL="shop@example.com"):
            response = self.client.post(
                shop_reverse("checkout:checkout"),
                _checkout_post_data(self.vrdnik.pk),
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            shop_reverse("checkout:success"),
        )
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.get()
        self.assertEqual(order.total, Decimal("1450.00"))
        self.assertEqual(order.requested_delivery_date, checkout_today())
        self.assertEqual(self.client.session.get(SESSION_KEY), {})

    def test_scheduled_delivery_checkout_has_free_shipping(self) -> None:
        future_date = min_scheduled_delivery_date()
        with self.settings(SHOP_NOTIFICATION_EMAIL="shop@example.com"):
            response = self.client.post(
                shop_reverse("checkout:checkout"),
                _checkout_post_data(
                    self.vrdnik.pk,
                    delivery_timing=DeliveryTiming.SCHEDULED,
                    requested_delivery_date=future_date.isoformat(),
                ),
            )

        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.shipping_price, Decimal("0"))
        self.assertEqual(order.total, Decimal("1000.00"))
        self.assertEqual(order.requested_delivery_date, future_date)

    def test_two_consecutive_orders_succeed(self) -> None:
        with self.settings(SHOP_NOTIFICATION_EMAIL="shop@example.com"):
            first = self.client.post(
                shop_reverse("checkout:checkout"),
                _checkout_post_data(self.vrdnik.pk),
            )
            self.assertEqual(first.status_code, 302)

            session = self.client.session
            session[SESSION_KEY] = {str(self.product.pk): 1}
            session.save()

            second = self.client.post(
                shop_reverse("checkout:checkout"),
                _checkout_post_data(self.vrdnik.pk, first_name="Mika"),
            )

        self.assertEqual(second.status_code, 302)
        self.assertEqual(Order.objects.count(), 2)
        self.assertEqual(
            Order.objects.order_by("pk").last().first_name,
            "Mika",
        )

    def test_checkout_error_does_not_show_validation_banner_for_valid_form(self) -> None:
        self.product.stock = 0
        self.product.save(update_fields=["stock"])

        response = self.client.post(
            shop_reverse("checkout:checkout"),
            _checkout_post_data(self.vrdnik.pk),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        self.assertNotContains(
            response,
            "Some fields need your attention",
        )
        self.assertContains(response, "Nema dovoljno")

    def test_logged_in_user_without_email_sees_email_field(self) -> None:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(
            username="noemail",
            password="secret123",
        )
        user.email = None
        user.save(update_fields=["email"])
        self.client.login(username="noemail", password="secret123")

        response = self.client.get(shop_reverse("checkout:checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="id_guest_email"')
        self.assertContains(response, 'type="email"')

    def test_logged_in_user_without_email_can_checkout(self) -> None:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(
            username="noemail2",
            password="secret123",
        )
        user.email = None
        user.save(update_fields=["email"])
        self.client.login(username="noemail2", password="secret123")

        with self.settings(SHOP_NOTIFICATION_EMAIL="shop@example.com"):
            response = self.client.post(
                shop_reverse("checkout:checkout"),
                _checkout_post_data(
                    self.vrdnik.pk,
                    guest_email="buyer@example.com",
                ),
            )

        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertIsNone(user.email)
        order = Order.objects.get()
        self.assertEqual(order.guest_email, "buyer@example.com")

    def test_logged_in_user_with_email_sees_email_field(self) -> None:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(
            username="hasemail",
            email="member@example.com",
            password="secret123",
        )
        self.client.login(username="hasemail", password="secret123")

        response = self.client.get(shop_reverse("checkout:checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="id_guest_email"')
        self.assertContains(response, 'type="email"')
        self.assertNotContains(response, "member@example.com")

    def test_logged_in_user_can_order_with_recipient_email(self) -> None:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(
            username="giftbuyer",
            email="member@example.com",
            password="secret123",
        )
        self.client.login(username="giftbuyer", password="secret123")

        with self.settings(SHOP_NOTIFICATION_EMAIL="shop@example.com"):
            response = self.client.post(
                shop_reverse("checkout:checkout"),
                _checkout_post_data(
                    self.vrdnik.pk,
                    guest_email="recipient@example.com",
                ),
            )

        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertEqual(user.email, "member@example.com")
        order = Order.objects.get()
        self.assertEqual(order.guest_email, "recipient@example.com")
        self.assertEqual(order.customer_email, "recipient@example.com")
