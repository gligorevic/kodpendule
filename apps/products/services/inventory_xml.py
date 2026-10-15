"""Bounded XML parsing, reviewable previews and atomic SKU-based stock imports.

No XML content or category IDs from the browser are trusted as product data.
An import never deletes products, and prices of existing products are preserved.
"""
from __future__ import annotations

from collections import Counter
from datetime import timedelta
from decimal import Decimal, InvalidOperation
import hashlib
from functools import lru_cache
import json
from pathlib import Path
import re
import unicodedata
from xml.etree import ElementTree

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext as _

from apps.categories.models import Category
from apps.products.models import Product, XMLImportBatch

MAX_XML_BYTES = 5 * 1024 * 1024
MAX_XML_ROWS = 10000
PREVIEW_LIFETIME = timedelta(hours=2)
NUMBER = re.compile(r"(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?\Z")


class InventoryImportError(ValueError):
    pass


@lru_cache(maxsize=1)
def _restricted_skus() -> set[str]:
    manifest = Path(__file__).resolve().parents[1] / "data" / "restricted_inventory_skus.json"
    return set(json.loads(manifest.read_text(encoding="utf-8"))) if manifest.exists() else set()


def restricted_product_reason(name: str, sku: str = "") -> str:
    """Conservative guard; reviewed source SKUs complement product-name matching."""
    if sku and sku in _restricted_skus():
        return _("Restricted product — excluded from import.")
    text = unicodedata.normalize("NFKD", name.upper()).encode("ascii", "ignore").decode()
    patterns = (
        r"\b(CIGARET\w*|DUVAN\w*|DUHAN\w*|TOBACCO|VAPE\w*|VAPOR\w*|IQOS|HEETS|TEREA|NEO|VE0|VEO|SNUS|NIKOTIN\w*)\b",
        r"\b(MARLBORO|WINSTON|CAMEL|LUCKY STRIKE|PALL MALL|DAVIDOFF|CHESTERFIELD|SOBRANIE|ROTHMANS|DUNHILL|L&M|PHILIP MORRIS)\b",
        r"^LD\b.*\b(SLIM\w*|VIOL\w*|PINK)\b",
        r"\b(PIVO|BEER|VINO|WINE|RAKIJA|VODKA|VOTKA|WHISKY|WHISKEY|VISKI|GIN|DZIN|TEQUILA|TEKILA|LIKER|KONJAK|BRANDY|VINJAK|VERMUT|BERMET|ORPHELINE|SPRITZ|PROSECCO|SAMPANJ\w*)\b",
        r"\bRUM\b(?!\s+(KASATO|PLOCICA|AROMA))",
        r"\b(HEINEKEN|TUBORG|LAV|ZAJECARSKO|JELEN|NIKSICKO|AMSTEL|CARLSBERG|STELLA ARTOIS|JACK DANIEL\w*|JOHNNIE WALKER|JAMESON|BALLANTINE\w*|SMIRNOFF|ABSOLUT|GORKI LIST|JAGERMEISTER|BAILEYS|APEROL|CAMPARI)\b",
        r"\bBAG IN BOX\b",
    )
    if any(re.search(pattern, text) for pattern in patterns):
        return _("Restricted product — excluded from import.")
    return ""


def _number(raw: str, field: str) -> Decimal:
    if not NUMBER.fullmatch(raw):
        raise InventoryImportError(_("Invalid number in %(field)s.") % {"field": field})
    try:
        return Decimal(raw.replace(",", ""))
    except InvalidOperation as exc:
        raise InventoryImportError(_("Invalid number in %(field)s.") % {"field": field}) from exc


def parse_inventory_xml(content: bytes) -> dict:
    """Return JSON-safe rows and quarantined records; malformed files fail closed."""
    if not content or len(content) > MAX_XML_BYTES:
        raise InventoryImportError(_("Upload a non-empty XML file up to 5 MB."))
    declaration = re.match(br"\s*<\?xml[^>]*encoding\s*=\s*['\"]([^'\"]+)", content[:200], re.I)
    encoding = declaration.group(1).decode("ascii", errors="replace").lower() if declaration else "utf-8-sig"
    allowed = {"utf-8", "utf-8-sig", "windows-1250", "cp1250"}
    if encoding not in allowed:
        raise InventoryImportError(_("Use UTF-8 or Windows-1250 XML encoding."))
    try:
        decoded = content.decode(encoding)
    except UnicodeError as exc:
        raise InventoryImportError(_("The XML encoding is invalid.")) from exc
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", decoded, re.I):
        raise InventoryImportError(_("XML documents with DTD or entities are not allowed."))
    try:
        root = ElementTree.fromstring(decoded)
    except (ElementTree.ParseError, ValueError) as exc:
        raise InventoryImportError(_("The XML document is malformed.")) from exc
    if root.tag != "ArtikliWeb" or any(item.tag != "artikal" for item in root):
        raise InventoryImportError(_("Expected ArtikliWeb with artikal records."))
    if not 0 < len(root) <= MAX_XML_ROWS:
        raise InventoryImportError(_("The XML must contain between 1 and 10,000 records."))
    rows, rejected = [], []
    seen = set()
    for number, item in enumerate(root, start=1):
        sku = (item.get("SifraArtikla") or "").strip()
        name = (item.findtext("NazivArtikla") or "").strip()
        barcode = (item.findtext("Barcode") or "").strip()
        if sku in seen and sku:
            raise InventoryImportError(_("Duplicate SKU %(sku)s. Correct the XML before importing.") % {"sku": sku})
        seen.add(sku)
        try:
            if not sku or not name or len(sku) > 64 or len(name) > 255 or len(barcode) > 64:
                raise InventoryImportError(_("Missing or overlong SKU, name or barcode."))
            if (any(len(child) for child in item)
                or len(item.findall("Barcode")) > 1
                or any(len(item.findall(tag)) != 1 for tag in ("NazivArtikla", "Cena", "Kolicina"))):
                raise InventoryImportError(_("Each record must have one name, price and quantity."))
            restricted = restricted_product_reason(name, sku)
            if restricted:
                raise InventoryImportError(restricted)
            price = _number((item.findtext("Cena") or "").strip(), "Cena")
            quantity = _number((item.findtext("Kolicina") or "").strip(), "Kolicina")
            if price > Decimal("9999999999.99"):
                raise InventoryImportError(_("Price exceeds the supported limit."))
            if quantity != quantity.to_integral_value() or quantity > 2147483647:
                raise InventoryImportError(_("Stock must be a non-negative whole number within the supported limit."))
            rows.append({"line": number, "sku": sku, "barcode": barcode, "name": name, "price": str(price.quantize(Decimal(".01"))), "stock": int(quantity)})
        except InventoryImportError as exc:
            rejected.append({"line": number, "sku": sku, "name": name, "reason": str(exc)})
    return {"rows": rows, "rejected": rejected, "total": len(root)}


def _authorize(user, *, adding=False):
    if not user.is_active or not user.is_staff or not user.has_perm("products.change_product"):
        raise PermissionDenied
    if adding and not user.has_perm("products.add_product"):
        raise PermissionDenied


def build_preview(content: bytes, *, user, filename="inventory.xml") -> XMLImportBatch:
    _authorize(user)
    payload = parse_inventory_xml(content)
    existing = Product.objects.filter(sku__in=[row["sku"] for row in payload["rows"]]).prefetch_related("translations").in_bulk(field_name="sku")
    barcode_owners = {}
    for product in Product.objects.exclude(barcode="").filter(barcode__in=[row["barcode"] for row in payload["rows"]]):
        barcode_owners.setdefault(product.barcode, set()).add(product.sku)
    source_barcodes = Counter(row["barcode"] for row in payload["rows"] if row["barcode"])
    accepted = []
    for row in payload["rows"]:
        product = existing.get(row["sku"])
        reason = ""
        if row["barcode"] and (barcode_owners.get(row["barcode"], set()) - {row["sku"]} or source_barcodes[row["barcode"]] > 1):
            reason = _("Barcode belongs to another SKU. Verify product identity before importing.")
        elif product and not _same_identity(product, row):
            reason = _("SKU matches a different product name or barcode. Verify product identity before importing.")
        if reason:
            payload["rejected"].append({"line": row["line"], "sku": row["sku"], "name": row["name"], "reason": str(reason)})
            continue
        row["before"] = None
        row["action"] = "new"
        if product:
            row["before"] = {"pk": product.pk, "stock": product.stock, "updated_at": product.updated_at.isoformat(), "barcode": product.barcode}
            row["action"] = "changed" if product.stock != row["stock"] else "unchanged"
            row["current_price"] = str(product.price)
        accepted.append(row)
    payload["rows"] = accepted
    payload["counts"] = dict(Counter(row["action"] for row in payload["rows"]))
    return XMLImportBatch.objects.create(
        created_by=user, filename=Path(filename).name[:255],
        file_sha256=hashlib.sha256(content).hexdigest(), payload=payload,
        expires_at=timezone.now() + PREVIEW_LIFETIME,
    )


def _same_identity(product, row):
    if product.barcode:
        return bool(row["barcode"]) and product.barcode == row["barcode"]
    normalize = lambda name: " ".join(unicodedata.normalize("NFKC", name).casefold().split())
    return any(normalize(trans.name) == normalize(row["name"]) for trans in product.translations.all())


def _check_batch(batch, user):
    _authorize(user)
    if batch.created_by_id != user.pk:
        raise PermissionDenied
    if not batch.applied_at and batch.expires_at <= timezone.now():
        raise InventoryImportError(_("This preview has expired. Upload the XML again."))


@transaction.atomic
def save_categories(batch_id, *, user, categories: dict) -> XMLImportBatch:
    batch = XMLImportBatch.objects.select_for_update().get(pk=batch_id)
    _check_batch(batch, user)
    if batch.applied_at:
        raise InventoryImportError(_("This import has already been applied."))
    _authorize(user, adding=bool(categories))
    new_skus = {row["sku"] for row in batch.payload["rows"] if row["action"] == "new"}
    if set(categories) - new_skus:
        raise InventoryImportError(_("Invalid category selection."))
    try:
        selected = {sku: int(pk) for sku, pk in categories.items() if pk}
    except (TypeError, ValueError) as exc:
        raise InventoryImportError(_("Invalid category selection.")) from exc
    valid_ids = set(Category.objects.filter(pk__in=selected.values(), is_active=True).values_list("pk", flat=True))
    if set(selected.values()) - valid_ids:
        raise InventoryImportError(_("Choose an active category for every new product."))
    for sku in categories:
        batch.categories.pop(sku, None)
    batch.categories.update(selected)
    batch.save(update_fields=["categories"])
    return batch


def apply_import(batch_id, *, user, acknowledge_rejected=False) -> dict:
    """One atomic change set; all checks precede writes and replay is a no-op."""
    try:
        with transaction.atomic():
            return _apply_locked(batch_id, user=user, acknowledge_rejected=acknowledge_rejected)
    except IntegrityError as exc:
        raise InventoryImportError(_("Products changed during import. Upload the XML again.")) from exc


def _apply_locked(batch_id, *, user, acknowledge_rejected):
    batch = XMLImportBatch.objects.select_for_update().get(pk=batch_id)
    _check_batch(batch, user)
    if batch.applied_at:
        return batch.result
    rows = batch.payload["rows"]
    new_rows = [row for row in rows if row["action"] == "new"]
    _authorize(user, adding=bool(new_rows))
    if batch.payload["rejected"] and not acknowledge_rejected:
        raise InventoryImportError(_("Confirm that the excluded records will be skipped."))
    if not rows:
        raise InventoryImportError(_("There are no valid records to import."))
    category_ids = {batch.categories.get(row["sku"]) for row in new_rows}
    valid_ids = set(Category.objects.select_for_update().filter(pk__in=category_ids - {None}, is_active=True).values_list("pk", flat=True))
    if category_ids - valid_ids:
        raise InventoryImportError(_("Choose an active category for every new product."))
    products = {
        product.sku: product for product in Product.objects.select_for_update()
        .filter(sku__in=[row["sku"] for row in rows]).prefetch_related("translations").order_by("pk")
    }
    barcode_owners = {}
    for product in Product.objects.exclude(barcode="").filter(barcode__in=[row["barcode"] for row in rows]):
        barcode_owners.setdefault(product.barcode, set()).add(product.sku)
    for row in rows:
        current = products.get(row["sku"])
        before = row["before"]
        if (before is None and current is not None) or (before is not None and (
            current is None or current.pk != before["pk"] or current.stock != before["stock"]
            or current.updated_at.isoformat() != before["updated_at"]
            or current.barcode != before["barcode"] or not _same_identity(current, row)
        )):
            raise InventoryImportError(_("Products changed after this preview. Upload the XML again; no changes were applied."))
        if row["barcode"] and barcode_owners.get(row["barcode"], set()) - {row["sku"]}:
            raise InventoryImportError(_("Barcode belongs to another SKU. Verify product identity before importing."))
        if restricted_product_reason(row["name"], row["sku"]):
            raise InventoryImportError(_("A restricted product was detected. Upload the XML again."))
    now = timezone.now()
    result = {"created": 0, "updated": 0, "unchanged": 0, "rejected": len(batch.payload["rejected"])}
    for row in rows:
        if row["action"] == "new":
            product = Product(category_id=batch.categories[row["sku"]], sku=row["sku"], barcode=row["barcode"], price=Decimal(row["price"]), stock=row["stock"])
            product.set_current_language("sr")
            product.name = row["name"]
            # SKU digest keeps long/identical names distinct and preserves leading-zero identity.
            base = slugify(row["name"].replace("đ", "dj").replace("Đ", "Dj"))[:230] or "artikal"
            suffix = hashlib.sha256(row["sku"].encode()).hexdigest()[:16]
            product.slug = f"{base}-{suffix}"
            product.save()
            result["created"] += 1
        elif row["action"] == "changed":
            current = products[row["sku"]]
            # Conditional update also protects SQLite, where SELECT FOR UPDATE is a no-op.
            changed = Product.objects.filter(pk=current.pk, stock=row["before"]["stock"], updated_at=current.updated_at).update(stock=row["stock"], updated_at=now)
            if changed != 1:
                raise InventoryImportError(_("Products changed during import. Upload the XML again."))
            result["updated"] += 1
        else:
            result["unchanged"] += 1
    batch.result = result
    batch.applied_at = now
    batch.save(update_fields=["result", "applied_at"])
    return result
