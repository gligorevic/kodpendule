import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.core.management import CommandError
from django.test import SimpleTestCase
from PIL import Image

from apps.core.management.commands.seed_local_preview import (
    APP_ROOT, assert_local_preview, inspect_asset, load_shipping,
)


class PreviewSafetyTests(SimpleTestCase):
    def test_unsafe_settings_are_rejected_before_storage_or_database_access(self):
        cases = [
            {"SETTINGS_MODULE": "config.settings.production"},
            {"DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql", "NAME": "production"}}},
            {"DATABASES": {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "/tmp/other.sqlite3"}}},
            {"STORAGES": {"default": {"BACKEND": "config.storage.R2Storage"}}},
            {"USE_R2": True},
            {"MEDIA_ROOT": "/tmp/outside-preview-media"},
            {"EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend"},
            {"DATABASE_ROUTERS": ["unexpected.router"]},
        ]
        base = {
            "SETTINGS_MODULE": "config.settings.preview",
            "LOCAL_CATALOG_PREVIEW": True,
            "BASE_DIR": APP_ROOT,
            "DATABASES": {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": APP_ROOT / "db.sqlite3"}},
            "DATABASE_ROUTERS": [],
            "MEDIA_ROOT": APP_ROOT / "media",
            "USE_R2": False,
            "EMAIL_BACKEND": "django.core.mail.backends.locmem.EmailBackend",
            "EMAIL_HOST": "",
            "SENDGRID_API_KEY": "",
            "STORAGES": {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}},
        }
        for changes in cases:
            with self.subTest(changes=changes), patch(
                "apps.core.management.commands.seed_local_preview.settings",
                SimpleNamespace(**(base | changes)),
            ), patch("apps.core.management.commands.seed_local_preview.storages") as storage:
                with self.assertRaises(CommandError):
                    assert_local_preview()
                storage.__getitem__.assert_not_called()

        for cached in (
            {"ENGINE": "django.db.backends.postgresql", "NAME": "production"},
            {"ENGINE": "django.db.backends.sqlite3", "NAME": "/tmp/other.sqlite3"},
            {"ENGINE": "django.db.backends.sqlite3", "NAME": APP_ROOT / "db.sqlite3", "OPTIONS": {"uri": True}},
        ):
            connection_handler = MagicMock()
            connection_handler.settings = {"default": cached}
            connection_handler.__getitem__.return_value.settings_dict = cached
            with self.subTest(cached=cached), patch(
                "apps.core.management.commands.seed_local_preview.settings", SimpleNamespace(**base)
            ), patch(
                "apps.core.management.commands.seed_local_preview.connections", connection_handler
            ), patch(
                "apps.core.management.commands.seed_local_preview.router", SimpleNamespace(routers=[])
            ), patch("apps.core.management.commands.seed_local_preview.storages") as storage:
                with self.assertRaisesMessage(CommandError, "cached nonlocal/custom"):
                    assert_local_preview()
                storage.__getitem__.assert_not_called()

    def test_asset_tampering_and_invalid_images_are_rejected(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "product.png"
            Image.new("RGB", (4, 4), "red").save(path)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(inspect_asset(path, digest)["suffix"], ".png")
            Image.new("RGB", (4, 4), "blue").save(path)
            with self.assertRaisesMessage(CommandError, "SHA-256 differs"):
                inspect_asset(path, digest)
            path.write_bytes(b"not an image")
            with self.assertRaises(CommandError):
                inspect_asset(path)

    def test_public_delivery_snapshot_preserves_prices_and_rejects_bad_rules(self):
        rules = {"base": "300.00", "threshold": "2000.00", "discounted_shipping_price": "150.00", "threshold_shipping_mode": "free"}
        snapshot = {
            "schema": 1, "currency": "RSD", "source_url": "https://www.kodpendule.com/placanje/",
            "semantics": {"same_day_threshold_inclusive": True, "future_scheduled_delivery_free": True},
            "cities": [{"name": "Vrdnik", "source_id": "1", **rules}],
            "raw_city_delivery": {"1": rules.copy()},
        }
        with TemporaryDirectory() as tmp:
            directory = Path(tmp)
            path = directory / "public-shipping-snapshot.json"
            self.assertIsNone(load_shipping(directory))
            path.write_text(json.dumps(snapshot))
            row = load_shipping(directory)[0]
            self.assertEqual(str(row["shipping_price"]), "300.00")
            self.assertEqual(str(row["promo_cart_threshold"]), "2000.00")
            self.assertEqual(str(row["promo_discounted_shipping_price"]), "150.00")
            self.assertEqual(row["promo_shipping_mode"], "free")
            for value in ("NaN", "-1", "0.001", "10000000000"):
                snapshot["cities"][0]["base"] = value
                snapshot["raw_city_delivery"]["1"]["base"] = value
                path.write_text(json.dumps(snapshot))
                with self.subTest(value=value), self.assertRaises(CommandError):
                    load_shipping(directory)
