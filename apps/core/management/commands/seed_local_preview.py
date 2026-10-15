"""Rebuild the local catalog preview from reviewed, offline catalog manifests."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import tarfile
import uuid

from PIL import Image
from django.conf import settings
from django.core.files.storage import FileSystemStorage, storages
from django.core.management import BaseCommand, CommandError, call_command
from django.db import connections, router, transaction
from django.utils.text import slugify

from apps.categories.models import Category
from apps.core.models import FooterSettings, SiteSettings
from apps.products.models import Product
from apps.products.services.inventory_xml import restricted_product_reason
from apps.shipping.models import City


APP_ROOT = Path(__file__).resolve().parents[4]
PANTRY = "Namirnice za pripremu jela"
PANTRY_FALLBACK = PANTRY + " > Osnovne namirnice i dodaci za kolače"


def assert_local_preview():
    """Fail before any DB access, file writes, migrations or model signals."""
    if (
        settings.SETTINGS_MODULE != "config.settings.preview"
        or not getattr(settings, "LOCAL_CATALOG_PREVIEW", False)
        or Path(settings.BASE_DIR).resolve() != APP_ROOT
        or set(settings.DATABASES) != {"default"}
        or settings.DATABASE_ROUTERS
    ):
        raise CommandError("Use only --settings=config.settings.preview for this command.")
    db = settings.DATABASES["default"]
    if (
        db["ENGINE"] != "django.db.backends.sqlite3"
        or Path(db["NAME"]).resolve() != APP_ROOT / "db.sqlite3"
        or (APP_ROOT / "db.sqlite3").is_symlink()
        or getattr(settings, "USE_R2", False)
        or Path(settings.MEDIA_ROOT).resolve() != APP_ROOT / "media"
        or (APP_ROOT / "media").is_symlink()
        or settings.EMAIL_BACKEND not in {
            "django.core.mail.backends.locmem.EmailBackend",
            "django.core.mail.backends.console.EmailBackend",
        }
        or settings.EMAIL_HOST
        or getattr(settings, "SENDGRID_API_KEY", "")
    ):
        raise CommandError("Preview requires the local SQLite DB, local media and offline email.")
    if settings.STORAGES["default"]["BACKEND"] != "django.core.files.storage.FileSystemStorage":
        raise CommandError("Preview refuses remote/custom storage.")
    # Django caches connection settings and routers. Check those as well as the
    # settings object, without opening a database connection.
    cached_databases = connections.settings
    if set(cached_databases) != {"default"} or router.routers:
        raise CommandError("Preview refuses cached extra databases or routers.")
    for configured in (cached_databases["default"], connections["default"].settings_dict):
        if (
            configured["ENGINE"] != "django.db.backends.sqlite3"
            or Path(configured["NAME"]).resolve() != APP_ROOT / "db.sqlite3"
            or configured.get("OPTIONS")
        ):
            raise CommandError("Preview refuses a cached nonlocal/custom database connection.")
    active = connections["default"].connection
    if active is not None:
        if type(active) is not sqlite3.Connection:
            raise CommandError("Preview refuses a non-SQLite open connection.")
        for _, alias, filename in active.execute("PRAGMA database_list"):
            if alias != "temp" and (alias != "main" or Path(filename).resolve() != APP_ROOT / "db.sqlite3"):
                raise CommandError("Preview refuses an open connection outside the local database.")
    if type(storages["default"]) is not FileSystemStorage:
        raise CommandError("Preview requires exact FileSystemStorage.")
    for model, field in ((Product, "main_image"), (Category, "image")):
        storage = model._meta.get_field(field).storage
        if storage.__class__ is not FileSystemStorage or Path(storage.location).resolve() != APP_ROOT / "media":
            raise CommandError("A catalog image field is not using the local media directory.")


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CommandError(f"Cannot read manifest {path.name}: {exc}") from exc


def inspect_asset(path, expected_hash=""):
    path = Path(path).resolve()
    try:
        data = path.read_bytes()
        if not 0 < len(data) <= 8 * 1024 * 1024:
            raise ValueError("image exceeds 8 MiB or is empty")
        digest = hashlib.sha256(data).hexdigest()
        if expected_hash and digest != expected_hash:
            raise ValueError("SHA-256 differs from reviewed manifest")
        with Image.open(path) as image:
            if image.format not in {"JPEG", "PNG", "WEBP"} or image.width * image.height > 16_000_000:
                raise ValueError("unsupported format/dimensions")
            suffix = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}[image.format]
            image.verify()
        return {"path": path, "sha256": digest, "suffix": suffix}
    except (OSError, ValueError) as exc:
        raise CommandError(f"Invalid local image {path}: {exc}") from exc


def load_catalog(directory):
    inventory = read_json(directory / "inventory-permitted.json")
    categories = read_json(directory / "category-image-plan.json")["records"]
    source_categories = read_json(directory / "initial-import-state.json")["categories"]
    uploads = read_json(directory / "category-upload-results.json")
    photos = read_json(directory / "images-ready-final.json")["records"]
    paths = {r["key"] for r in categories}
    if len(paths) != len(categories) or paths != set(source_categories):
        raise CommandError("Category manifests disagree or contain duplicates.")
    by_path = {r["key"]: r for r in categories}
    for row in categories:
        if str(row["id"]) != str(source_categories[row["key"]]):
            raise CommandError("Category source ID does not match the reviewed import.")
        parent_path = row["key"].rsplit(" > ", 1)[0] if " > " in row["key"] else ""
        if parent_path and parent_path not in paths:
            raise CommandError("Category has an unknown parent.")
        if uploads.get(str(row["id"]), {}).get("status") not in {"uploaded", "preserved_existing"}:
            raise CommandError("Category does not have a reviewed image result.")
        row["parent_path"] = parent_path
        local_path = row.get("local_path")
        if not local_path and row["key"] == PANTRY:
            # The existing local media contains test fixtures, not the live root image.
            local_path = by_path[PANTRY_FALLBACK]["local_path"]
        if not local_path:
            raise CommandError(f"No local image for category {row['key']}.")
        row["asset_local"] = inspect_asset(local_path, row.get("asset", {}).get("sha256", ""))
    seen_skus, seen_barcodes = set(), set()
    for row in inventory:
        sku, barcode = str(row["sku"]), str(row.get("barcode", ""))
        if not sku or sku in seen_skus or (barcode and barcode in seen_barcodes):
            raise CommandError("Inventory contains a missing/duplicate SKU or barcode.")
        if restricted_product_reason(row["name"], sku):
            raise CommandError(f"Restricted product in permitted inventory: {sku}.")
        seen_skus.add(sku)
        if barcode:
            seen_barcodes.add(barcode)
        path = row["category"] + (" > " + row["subcategory"] if row.get("subcategory") else "")
        if path not in paths:
            raise CommandError(f"Unknown category for SKU {sku}.")
        try:
            price, stock = Decimal(row["price"]), Decimal(row["stock"])
            if not price.is_finite() or not stock.is_finite() or price < 0 or stock < 0 or stock != int(stock):
                raise ValueError("invalid price/stock")
        except (InvalidOperation, ValueError) as exc:
            raise CommandError(f"Invalid price/stock for SKU {sku}.") from exc
        row.update(category_path=path, price_value=price, stock_value=int(stock))
    photo_map = {}
    for row in photos:
        sku = str(row["sku"])
        if row.get("status") != "verified" or sku not in seen_skus or sku in photo_map:
            raise CommandError("Photo manifest contains unverified, duplicate or unknown SKU.")
        row["asset_local"] = inspect_asset(row["local_path"], row.get("asset", {}).get("sha256", ""))
        photo_map[sku] = row
    return inventory, sorted(categories, key=lambda r: (r["key"].count(" > "), int(r["fields"].get("sort_order", 0)))), photo_map


def backup_local_state(directory):
    assert_local_preview()
    destination = directory / "preview-backups" / (datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6])
    destination.mkdir(parents=True)
    database = APP_ROOT / "db.sqlite3"
    if database.exists():
        with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as source:
            with sqlite3.connect(destination / "db.sqlite3") as target:
                source.backup(target)
    media = APP_ROOT / "media"
    if media.exists():
        with tarfile.open(destination / "media.tar.gz", "w:gz") as archive:
            archive.add(media, arcname="media")
    (destination / "metadata.json").write_text(json.dumps({"database": str(database), "media": str(media)}, indent=2))
    return destination


def copy_asset(asset, group, identifier):
    safe_id = hashlib.sha256(identifier.encode()).hexdigest()[:16]
    name = f"{group}/preview/{safe_id}-{asset['sha256'][:16]}{asset['suffix']}"
    media = APP_ROOT / "media"
    target = media / name
    if not target.resolve().is_relative_to(media):
        raise CommandError("Refusing a media path outside local media.")
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == asset["sha256"]:
        return name
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        shutil.copyfile(asset["path"], temporary)
        if hashlib.sha256(temporary.read_bytes()).hexdigest() != asset["sha256"]:
            raise CommandError("Source image changed after validation.")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return name


def seed_catalog(inventory, categories, photos):
    assert_local_preview()
    local_categories = {}
    with transaction.atomic():
        for row in categories:
            fields = row["fields"]
            parent = local_categories.get(row["parent_path"])
            matches = list(Category.objects.filter(parent=parent, translations__language_code="sr", translations__name=fields["name_sr"]))
            if len(matches) > 1:
                raise CommandError(f"Ambiguous existing category {row['key']}.")
            category = matches[0] if matches else Category(parent=parent)
            category.set_current_language("sr")
            category.name = fields["name_sr"]
            category.slug = fields["slug_sr"]
            category.description = fields.get("description_sr", "")
            category.is_active = True
            category.sort_order = int(fields.get("sort_order", 0))
            category.image = copy_asset(row["asset_local"], "categories", row["key"])
            category.save()
            local_categories[row["key"]] = category
        # Archive stale local products; never delete rows referenced by local orders.
        Product.objects.exclude(sku__in=[r["sku"] for r in inventory]).update(is_archived=True, is_recommended=False)
        for row in inventory:
            product = Product.objects.filter(sku=row["sku"]).first() or Product(sku=row["sku"])
            product.set_current_language("sr")
            product.name = row["name"]
            if not product.slug:
                base = slugify(row["name"].replace("đ", "dj").replace("Đ", "Dj"))[:200] or "artikal"
                product.slug = base + "-" + hashlib.sha256(row["sku"].encode()).hexdigest()[:16]
            product.barcode = row["barcode"]
            product.category = local_categories[row["category_path"]]
            product.price = row["price_value"]
            product.stock = row["stock_value"]
            product.discount_price = None
            product.is_archived = False
            product.is_recommended = False
            photo = photos.get(row["sku"])
            product.main_image = copy_asset(photo["asset_local"], "products", row["sku"]) if photo else ""
            product.main_image_source_url = (photo.get("attribution_source_url") or photo.get("source_url", "")) if photo else ""
            product.main_image_attribution = (photo.get("attribution_text") or photo.get("source_name") or photo.get("source", ""))[:255] if photo else ""
            product.main_image_license_url = photo.get("license_url", "") if photo else ""
            product.save()
        site = SiteSettings.load()
        site.set_current_language("sr")
        site.site_name = "Kod Pendule"
        site.default_meta_title = "Kod Pendule. prodavnica u Vrdniku"
        site.default_meta_description = "Namirnice, piće, slatkiši i proizvodi za domaćinstvo. Kod Pendule, Karađorđeva 11, Vrdnik."
        site.save()
        footer = FooterSettings.load()
        footer.set_current_language("sr")
        # Public contact page, checked 2026-10-15; no customer/admin data involved.
        footer.phone = "+381 62 164 2224"
        footer.email = "kodpendule@gmail.com"
        footer.address = "Karađorđeva 11\n22408 Vrdnik"
        footer.working_hours = "Svakog dana: 07:00–24:00"
        footer.save()
    return local_categories


def load_shipping(directory):
    """Read a reviewed public checkout snapshot; never fetch or infer tariffs."""
    path = directory / "public-shipping-snapshot.json"
    if not path.exists():
        return None
    snapshot = read_json(path)
    if (
        snapshot.get("schema") != 1
        or snapshot.get("currency") != "RSD"
        or snapshot.get("source_url") != "https://www.kodpendule.com/placanje/"
        or snapshot.get("semantics") != {
            "same_day_threshold_inclusive": True,
            "future_scheduled_delivery_free": True,
        }
    ):
        raise CommandError("Unreviewed or incompatible public delivery snapshot.")
    rows, names, ids = [], set(), set()
    raw = snapshot.get("raw_city_delivery", {})
    for order, row in enumerate(snapshot.get("cities", [])):
        try:
            name, source_id = row["name"].strip(), row["source_id"]
            mode = row["threshold_shipping_mode"]
            source_rule = {key: row[key] for key in (
                "base", "threshold", "discounted_shipping_price", "threshold_shipping_mode"
            )}
            if (
                not name or len(name) > 120 or name in names or source_id in ids
                or source_rule != raw[source_id] or mode not in {"free", "discounted"}
            ):
                raise ValueError("duplicate city or inconsistent source rule")
            values = {}
            for source, target in (
                ("base", "shipping_price"),
                ("threshold", "promo_cart_threshold"),
                ("discounted_shipping_price", "promo_discounted_shipping_price"),
            ):
                value = None if row[source] == "" and source != "base" else Decimal(row[source])
                if value is not None and (
                    not value.is_finite() or value < 0 or value >= Decimal("10000000000")
                    or value != value.quantize(Decimal("0.01"))
                ):
                    raise ValueError("invalid monetary amount")
                values[target] = value
            if mode == "discounted" and values["promo_cart_threshold"] and values["promo_discounted_shipping_price"] is None:
                raise ValueError("discounted rule has no tariff")
        except (KeyError, TypeError, AttributeError, InvalidOperation, ValueError) as exc:
            raise CommandError("Incomplete or invalid public delivery rule.") from exc
        names.add(name)
        ids.add(source_id)
        rows.append({"name": name, "sort_order": order, "promo_shipping_mode": mode, **values})
    if not rows or set(raw) != ids:
        raise CommandError("Delivery snapshot has missing city labels or rules.")
    return rows


def seed_shipping(rows):
    assert_local_preview()
    if rows is None:
        return
    with transaction.atomic():
        # Keep rows referenced by any local demo order, but mirror public options.
        City.objects.exclude(name__in=[row["name"] for row in rows]).update(is_active=False)
        for row in rows:
            city = City.objects.filter(name=row["name"]).first() or City(name=row["name"])
            if not city.slug:
                base = slugify(row["name"].replace("đ", "dj").replace("Đ", "Dj"))[:100] or "grad"
                city.slug = base + "-" + hashlib.sha256(row["name"].encode()).hexdigest()[:12]
            for field, value in row.items():
                setattr(city, field, value)
            city.is_active = True
            city.full_clean()
            city.save()


class Command(BaseCommand):
    help = "Seed an offline-only local preview from reviewed catalog manifests, backing up SQLite/media first."
    requires_system_checks = []
    requires_migrations_checks = False

    def add_arguments(self, parser):
        parser.add_argument("--catalog-dir", type=Path, default=APP_ROOT.parent / "catalog-work")

    def handle(self, *args, **options):
        assert_local_preview()
        directory = options["catalog_dir"].resolve()
        inventory, categories, photos = load_catalog(directory)
        shipping = load_shipping(directory)
        backup = backup_local_state(directory)
        self.stdout.write(f"Backup: {backup}")
        call_command("migrate", interactive=False, verbosity=0)
        local_categories = seed_catalog(inventory, categories, photos)
        seed_shipping(shipping)
        report = {
            "settings": settings.SETTINGS_MODULE,
            "database": str(APP_ROOT / "db.sqlite3"),
            "media_root": str(APP_ROOT / "media"),
            "backup": str(backup),
            "products": len(inventory),
            "product_images": len(photos),
            "categories": len(local_categories),
            "category_images": sum(bool(c.image) for c in local_categories.values()),
            "active_delivery_zones": City.objects.filter(is_active=True).count(),
            "delivery_source": "public-shipping-snapshot.json" if shipping is not None else "Existing local rules preserved (no public snapshot).",
            "contact_source": "https://www.kodpendule.com/kontakt/",
            "pantry_image": "Existing approved basic-ingredients category illustration used locally.",
            "notes": "No production connections, users or orders imported. No discounts/recommendations or delivery tariffs invented. Public shipping rules are copied only from the reviewed offline snapshot.",
        }
        (directory / "local-preview-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
        self.stdout.write(self.style.SUCCESS(json.dumps(report, ensure_ascii=False, indent=2)))
