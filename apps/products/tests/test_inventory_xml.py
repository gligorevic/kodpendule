from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse
from django.urls import resolve
from django.utils import timezone

from apps.categories.models import Category
from apps.core.storefront_urls import shop_reverse
from apps.products.models import Product, XMLImportBatch
from apps.products.services.inventory_xml import (
    InventoryImportError, apply_import, build_preview, parse_inventory_xml,
    save_categories,
)


def xml(*records, encoding="utf-8"):
    body = "".join(
        '<artikal SifraArtikla="{sku}"><Barcode>{barcode}</Barcode><NazivArtikla>{name}</NazivArtikla><Cena>{price}</Cena><Kolicina>{stock}</Kolicina></artikal>'.format(
            **{"sku": "001", "barcode": "0123456789012", "name": "Čokolada 100g", "price": "1,234.56", "stock": "8.00", **record}
        ) for record in records
    )
    return (f'<?xml version="1.0" encoding="{encoding}"?><ArtikliWeb>{body}</ArtikliWeb>').encode(encoding)


class InventoryXMLParserTests(SimpleTestCase):
    def test_windows_encoding_and_leading_zero_identifiers(self):
        parsed = parse_inventory_xml(xml({}, encoding="windows-1250"))
        row = parsed["rows"][0]
        self.assertEqual((row["sku"], row["barcode"], row["name"], row["price"], row["stock"]), ("001", "0123456789012", "Čokolada 100g", "1234.56", 8))

    def test_bad_row_quarantined_without_losing_valid_rows(self):
        parsed = parse_inventory_xml(xml({"sku": "", "name": ""}, {}))
        self.assertEqual(len(parsed["rows"]), 1)
        self.assertEqual(parsed["rejected"][0]["line"], 1)

    def test_invalid_and_fractional_quantities_are_never_rounded(self):
        for quantity in ("-1", "1.5", "NaN", "Infinity", "1,5", "2,147,483,648", ""):
            with self.subTest(quantity=quantity):
                parsed = parse_inventory_xml(xml({"stock": quantity}))
                self.assertEqual(parsed["rows"], [])
                self.assertEqual(len(parsed["rejected"]), 1)

    def test_prices_validate_grouping_and_bounds(self):
        for price in ("-1", "1,20.00", "1.234,50", "10000000000", "1.001", "NaN"):
            with self.subTest(price=price):
                self.assertEqual(parse_inventory_xml(xml({"price": price}))["rows"], [])

    def test_duplicate_sku_rejects_entire_document(self):
        with self.assertRaises(InventoryImportError):
            parse_inventory_xml(xml({}, {"name": "Druga čokolada"}))

    def test_zero_is_valid_sku_and_stock(self):
        self.assertEqual(parse_inventory_xml(xml({"sku": "0", "stock": "0.00"}))["rows"][0]["stock"], 0)

    def test_rejects_entities_and_wrong_shape(self):
        documents = (
            b'<!DOCTYPE ArtikliWeb [<!ENTITY e "attack">]><ArtikliWeb/>',
            b'<other/>', b'<ArtikliWeb><wrong/></ArtikliWeb>', b'<ArtikliWeb>',
            b'<ArtikliWeb/>', b'', b'<?xml version="1.0" encoding="utf-16"?><ArtikliWeb/>',
        )
        for content in documents:
            with self.subTest(content=content):
                with self.assertRaises(InventoryImportError):
                    parse_inventory_xml(content)

    def test_duplicate_barcode_is_quarantined(self):
        content = xml({}).replace(b"</Barcode>", b"</Barcode><Barcode>another</Barcode>")
        result = parse_inventory_xml(content)
        self.assertEqual(result["rows"], [])
        self.assertEqual(len(result["rejected"]), 1)

    def test_file_and_row_limits(self):
        with patch("apps.products.services.inventory_xml.MAX_XML_BYTES", 20):
            with self.assertRaises(InventoryImportError):
                parse_inventory_xml(xml({}))
        with patch("apps.products.services.inventory_xml.MAX_XML_ROWS", 1):
            with self.assertRaises(InventoryImportError):
                parse_inventory_xml(xml({}, {"sku": "002"}))

    def test_restricted_products_excluded_without_false_positives(self):
        for name in ("Marlboro gold", "Vape strawberry"):
            self.assertEqual(parse_inventory_xml(xml({"name": name}))["rows"], [])
        for name in ("WHISKAS PILETINA", "Rum Kasato", "Ld kese za smeće 40L"):
            self.assertEqual(len(parse_inventory_xml(xml({"name": name}))["rows"]), 1)

    def test_alcohol_names_and_previously_excluded_skus_are_accepted(self):
        for sku, name in (
            ("00001", "BERMET CRVENI 0.5"),
            ("00002", "ORPHELINE BELI PET2L"),
            ("00006", "BAG IN BOX BELI 3L"),
            ("00010", "GIFT BOX FRESCO 0.75"),
            ("0002140", "PLAVI GIN 0.7L"),
            ("NEW-BEER", "Pivo 0.5L"),
            ("NEW-WINE", "Vino belo"),
            ("NEW-SPIRIT", "WHISKY 0.7L"),
        ):
            with self.subTest(sku=sku, name=name):
                parsed = parse_inventory_xml(xml({"sku": sku, "name": name}))
                self.assertEqual(len(parsed["rows"]), 1)
                self.assertEqual(parsed["rejected"], [])


class InventoryXMLImportTests(TestCase):
    def setUp(self):
        # Parler's global cache outlives TestCase database rollbacks and reused PKs.
        cache.clear()
        self.user = get_user_model().objects.create_superuser("inventory-admin", "inventory@test.test", "pass")
        self.category = Category.objects.create()
        self.category.set_current_language("sr")
        self.category.name = "Slatkiši"
        self.category.slug = "slatkisi"
        self.category.save()
        self.product = Product(category=self.category, sku="001", barcode="0123456789012", price=Decimal("900.00"), stock=3)
        self.product.set_current_language("sr")
        self.product.name = "Čokolada 100g"
        self.product.slug = "cokolada"
        self.product.save()

    def preview(self, *records):
        return build_preview(xml(*(records or ({},))), user=self.user)

    def test_preview_has_no_product_side_effects(self):
        batch = self.preview()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(batch.payload["counts"], {"changed": 1})

    def test_stock_only_update_preserves_metadata_and_price(self):
        batch = self.preview({"name": "Čokolada novi opis"})
        result = apply_import(batch.pk, user=self.user)
        self.product.refresh_from_db()
        self.assertEqual((self.product.stock, self.product.price, self.product.name), (8, Decimal("900.00"), "Čokolada 100g"))
        self.assertEqual(result["updated"], 1)

    def test_noop_does_not_write_product_timestamp(self):
        before = self.product.updated_at
        batch = self.preview({"stock": "3"})
        result = apply_import(batch.pk, user=self.user)
        self.product.refresh_from_db()
        self.assertEqual(self.product.updated_at, before)
        self.assertEqual(result["unchanged"], 1)

    def test_alcohol_creation_then_stock_refresh(self):
        record = {"sku": "00001", "barcode": "9876543210123", "name": "BERMET CRVENI 0.5"}
        batch = self.preview(record)
        with self.assertRaises(InventoryImportError):
            apply_import(batch.pk, user=self.user)
        save_categories(batch.pk, user=self.user, categories={"00001": self.category.pk})
        self.assertEqual(apply_import(batch.pk, user=self.user)["created"], 1)
        batch = self.preview({**record, "stock": "12", "price": "999.00"})
        self.assertEqual(apply_import(batch.pk, user=self.user)["updated"], 1)
        product = Product.objects.get(sku="00001")
        self.assertEqual(product.stock, 12)
        self.assertEqual(product.price, Decimal("1234.56"))

    def test_new_product_requires_category_and_preserves_identifiers(self):
        batch = self.preview({"sku": "000NEW02", "barcode": "0000000123456"})
        with self.assertRaises(InventoryImportError):
            apply_import(batch.pk, user=self.user)
        self.assertFalse(Product.objects.filter(sku="000NEW02").exists())
        save_categories(batch.pk, user=self.user, categories={"000NEW02": self.category.pk})
        apply_import(batch.pk, user=self.user)
        product = Product.objects.get(sku="000NEW02")
        self.assertEqual((product.barcode, product.stock, product.price, product.category_id), ("0000000123456", 8, Decimal("1234.56"), self.category.pk))
        self.assertEqual(product.safe_translation_getter("name", language_code="sr"), "Čokolada 100g")
        url = product.get_absolute_url()
        self.assertEqual(resolve(url).kwargs["slug"], product.slug)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get(shop_reverse("products:list")).status_code, 200)

    def test_replay_is_idempotent_even_after_stock_changes(self):
        batch = self.preview()
        first = apply_import(batch.pk, user=self.user)
        Product.objects.filter(pk=self.product.pk).update(stock=4)
        self.assertEqual(apply_import(batch.pk, user=self.user), first)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 4)

    def test_late_database_failure_rolls_back_preceding_stock_change(self):
        batch = self.preview({}, {"sku": "000NEW02", "barcode": "222"})
        save_categories(batch.pk, user=self.user, categories={"000NEW02": self.category.pk})
        with patch.object(Product, "save", side_effect=IntegrityError("concurrent insert")):
            with self.assertRaises(InventoryImportError):
                apply_import(batch.pk, user=self.user)
        self.product.refresh_from_db()
        batch.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertIsNone(batch.applied_at)
        self.assertFalse(Product.objects.filter(sku="000NEW02").exists())

    def test_stale_checkout_stock_blocks_entire_import(self):
        batch = self.preview({}, {"sku": "000NEW02", "barcode": "222"})
        save_categories(batch.pk, user=self.user, categories={"000NEW02": self.category.pk})
        Product.objects.filter(pk=self.product.pk).update(stock=2)
        with self.assertRaises(InventoryImportError):
            apply_import(batch.pk, user=self.user)
        self.assertFalse(Product.objects.filter(sku="000NEW02").exists())
        batch.refresh_from_db()
        self.assertIsNone(batch.applied_at)

    def test_stale_metadata_and_expired_batch_block_import(self):
        batch = self.preview()
        Product.objects.filter(pk=self.product.pk).update(updated_at=timezone.now())
        with self.assertRaises(InventoryImportError):
            apply_import(batch.pk, user=self.user)
        batch = self.preview()
        XMLImportBatch.objects.filter(pk=batch.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        with self.assertRaises(InventoryImportError):
            apply_import(batch.pk, user=self.user)

    def test_identity_conflict_is_quarantined(self):
        self.product.barcode = ""
        self.product.name = "Pirinač"
        self.product.save()
        batch = self.preview()
        self.assertEqual(batch.payload["rows"], [])
        self.assertEqual(len(batch.payload["rejected"]), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)

    def test_empty_existing_barcode_allows_exact_name_match(self):
        self.product.barcode = ""
        self.product.save()
        self.assertEqual(self.preview().payload["counts"], {"changed": 1})

    def test_barcode_conflict_and_duplicate_source_barcode_are_quarantined(self):
        self.assertFalse(self.preview({"sku": "002"}).payload["rows"])
        batch = self.preview({}, {"sku": "002"})
        self.assertEqual(len(batch.payload["rejected"]), 2)

    def test_category_validation_and_permission(self):
        batch = self.preview({"sku": "002", "barcode": "222"})
        for selections in ({"bad-sku": self.category.pk}, {"002": "nonsense"}, {"002": 999999}):
            with self.assertRaises(InventoryImportError):
                save_categories(batch.pk, user=self.user, categories=selections)
        save_categories(batch.pk, user=self.user, categories={"002": self.category.pk})
        self.category.is_active = False
        self.category.save()
        with self.assertRaises(InventoryImportError):
            apply_import(batch.pk, user=self.user)

    def test_skip_requires_acknowledgement(self):
        batch = self.preview({}, {"sku": "", "name": ""})
        with self.assertRaises(InventoryImportError):
            apply_import(batch.pk, user=self.user)
        self.assertEqual(apply_import(batch.pk, user=self.user, acknowledge_rejected=True)["rejected"], 1)

    def test_batches_belong_to_creator(self):
        other = get_user_model().objects.create_superuser("other", "other@test.test", "pass")
        batch = self.preview()
        with self.assertRaises(PermissionDenied):
            apply_import(batch.pk, user=other)

    def test_change_only_user_can_refresh_but_cannot_add(self):
        staff = get_user_model().objects.create_user("staff", is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename="change_product"))
        batch = build_preview(xml({}), user=staff)
        self.assertEqual(apply_import(batch.pk, user=staff)["updated"], 1)
        batch = build_preview(xml({"sku": "002", "barcode": "222"}), user=staff)
        with self.assertRaises(PermissionDenied):
            save_categories(batch.pk, user=staff, categories={"002": self.category.pk})

    def test_deleted_or_concurrently_created_sku_blocks_apply(self):
        batch = self.preview()
        self.product.delete()
        with self.assertRaises(InventoryImportError):
            apply_import(batch.pk, user=self.user)


class InventoryXMLAdminTests(TestCase):
    preview = InventoryXMLImportTests.preview

    def setUp(self):
        InventoryXMLImportTests.setUp(self)
        self.client.force_login(self.user)
        self.url = reverse("admin:products_product_import_xml")

    def test_upload_preview_category_apply_flow(self):
        response = self.client.post(self.url, {"xml_file": SimpleUploadedFile("inventory.xml", xml({}, {"sku": "002", "barcode": "222"}))})
        self.assertEqual(response.status_code, 302)
        preview_url = response["Location"]
        response = self.client.get(preview_url)
        self.assertContains(response, 'name="category_2"')
        self.assertContains(response, "Čokolada 100g")
        response = self.client.post(preview_url, {"action": "categories", "category_2": self.category.pk})
        self.assertEqual(response.status_code, 302)
        response = self.client.post(preview_url, {"action": "apply"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Product.objects.get(sku="002").stock, 8)
        self.assertEqual(self.client.get(preview_url).status_code, 200)

    def test_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(self.url, {"xml_file": SimpleUploadedFile("inventory.xml", xml({}))})
        self.assertEqual(response.status_code, 403)

    def test_staff_without_product_permission_denied(self):
        staff = get_user_model().objects.create_user("no-permissions", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_other_admin_cannot_view_batch(self):
        batch = self.preview()
        other = get_user_model().objects.create_superuser("other", "other@test.test", "pass")
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse("admin:products_product_xml_preview", args=[batch.pk])).status_code, 404)

    def test_category_page_limit_keeps_forms_bounded(self):
        content = xml(*[{"sku": f"N-{n}", "barcode": f"NEW{n}"} for n in range(55)])
        batch = build_preview(content, user=self.user)
        url = reverse("admin:products_product_xml_preview", args=[batch.pk])
        response = self.client.get(url)
        self.assertEqual(len(response.context["table_rows"]), 50)
        self.assertEqual(len(response.context["category_form"].fields), 50)
        selections = {f"category_{n+1}": self.category.pk for n in range(50)}
        self.client.post(url, {"action": "categories", **selections})
        batch.refresh_from_db()
        self.assertEqual(len(batch.categories), 50)
        response = self.client.get(url + "?page=2")
        self.assertEqual(len(response.context["table_rows"]), 5)
        self.assertEqual(response.context["remaining"], 5)
