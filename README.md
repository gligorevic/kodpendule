# Kod Pendule — Webshop

Multilingual (Serbian / English) e-commerce for Serbia.  
**Stack:** Django 5 · SQLite (local) / PostgreSQL (Render) · django-parler · Bootstrap 5 · DRF · WhiteNoise · Gunicorn.

## Project root

This folder is the **Git repository root** and the **Django project root** (where `manage.py` lives).

`E:\Stefan Spremo\Firme\Projekti\Web development\Kod Pendule\kodpendule`

Open this folder in Cursor (**File → Open Folder**). Use the Python interpreter at `.venv\Scripts\python.exe`.

## Quick start

```powershell
cd "E:\Stefan Spremo\Firme\Projekti\Web development\Kod Pendule\kodpendule"
.\.venv\Scripts\Activate.ps1
pip install -r requirements/local.txt
copy .env.local.example .env.local
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Local database: **`db.sqlite3`** (created automatically).  
Detailed setup: **[docs/SETUP.md](docs/SETUP.md)**

Run the full test suite:

```powershell
python manage.py test apps config
```

### Storefront translations (Serbian Latin)

After any task that adds or changes translatable UI strings, agents must automatically:

1. `python manage.py makemessages -l sr`
2. Add/fill new entries in `scripts/fill_sr_translations.py` and run that script
3. `python manage.py compilemessages -l sr`

Full steps (dedupe, admin merge): **[docs/ADMIN_LOCALE.md](docs/ADMIN_LOCALE.md)** · **`.cursor/rules/i18n-after-changes.mdc`**

## Settings

| Module | Use | Database |
|--------|-----|----------|
| `config.settings.local` | Development | SQLite |
| `config.settings.production` | Render / Gunicorn | PostgreSQL |

Copy `.env.local.example` → `.env.local` for local development.

### Render (production)

Use **Python 3.12** (not 3.14). New Render services default to 3.14, which breaks Django admin changelist pages. The repo pins `3.12.11` via `.python-version` and `PYTHON_VERSION` in `render.yaml`. After deploy, confirm build logs show Python 3.12.x. If not, set **Environment → `PYTHON_VERSION` = `3.12.11`** in the Render dashboard and redeploy.

## Status

| Step | Description | Status |
|------|-------------|--------|
| 1–3 | Structure, models, settings | Done |
| 4 | Authentication | Done |
| 5 | Storefront (catalog, search, homepage) | Done |
| 6 | Cart & checkout (guest, COD) | Done |
| 7 | Order tracking & customer history | Done |
| 8 | Admin analytics dashboard | Done |
| 9+ | i18n URLs, … | Pending |

### Admin Serbian labels

Admin UI uses English `gettext` msgids and Serbian translations in `locale/sr/LC_MESSAGES/`. After editing `django.po`, compile:

```powershell
python manage.py compilemessages -l sr
```

On Windows without GNU gettext (`msgfmt`), use the project script instead (updates `django.po` storefront strings and compiles `django.mo`):

```powershell
python scripts/compile_sr_messages.py
```

### Analytics dashboard (Step 8)

Staff only: **[http://127.0.0.1:8000/admin/analitika/](http://127.0.0.1:8000/admin/analitika/)** (link also in admin header).

Filters: last 7/30/90 days, current month/year, specific month+year, or custom date range.

### Inventory XML import

After applying migrations, open **Products → Uvoz XML stanja artikala** in admin
(`/admin/proizvodi/import-xml/`). Drag in `StanjeArtikalaWeb.xml` or select it,
then review the preview. Supported uploads are UTF-8 or Windows-1250, up to
5 MB and 10,000 records. SKU and barcode identifiers retain leading zeros.

Choose an active category for every new product and **save categories on each
page** (50 rows per page). Review excluded records, acknowledge them, and apply
the import. New products use XML names, barcodes, prices and stock. Existing
products receive stock changes only; prices, discounts, descriptions, images,
barcodes and categories remain unchanged. Products absent from the XML are not
deleted or set to zero.

Before the first import, reconcile any legacy SKU values with the real product
identities and barcodes. Matching requires the same SKU and barcode, or an exact
normalized name when the existing barcode is empty. Conflicting names/barcodes,
invalid rows, fractional/negative quantities and restricted products are
excluded with reasons. Duplicate SKUs invalidate the file. No rounding or fuzzy
identity matching is performed.

Example or retired products can be marked **Archived** in their admin editor.
They remain available in admin and order history but are hidden from storefront
lists, search and product pages, and cannot be purchased from a previously saved
cart. New and existing products default to unarchived. To restore an archived
product, clear **Archived** in admin; the archive filter helps locate it. Reserve
legacy/example SKU values before importing a different real product with the
same source SKU.

Only staff with product-change permission can import; creating products also
requires product-add permission. Previews belong to their creator and expire
after two hours. Applying is atomic and checks for changed stock or identities;
if another order or edit changes a product after preview, upload the file again.
Reapplying the same completed preview is a no-op. The recent-import list retains
the preview, chosen categories and result for review.

Verified catalog-photo clients can POST multipart `sku`, `barcode` and `image`
to `/admin/proizvodi/import-image/` with an authenticated staff session,
product-change permission and a CSRF token. The endpoint requires an exact
SKU/barcode match, accepts JPEG, PNG or WebP up to 8 MB and 16 megapixels, and
fills only an empty main image. It locks the product and updates only the image
and timestamp, preserving current stock, prices and other catalog fields.
Existing photos are retained; deliberate replacements use the product editor.
Optional `main_image_source_url`, `main_image_attribution` and
`main_image_license_url` fields retain source/author/license evidence with the
photo. When provided, the product page shows an escaped attribution caption with
HTTP(S) source and license links. Only supply licensing information supported by
the source; the system does not infer a license from a retailer URL.

### Order tracking (Step 7)

| URL | Description |
|-----|-------------|
| `/narudzbina/pracenje/` | Guest track (order number + email) |
| `/narudzba/<order_number>/` | Order detail (after track, checkout, or login) |
| `/nalog/narudzbine/` | Logged-in order history |
