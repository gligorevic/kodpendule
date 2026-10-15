# Local catalog preview

From the repository directory:

```sh
.venv/bin/python manage.py seed_local_preview --settings=config.settings.preview
.venv/bin/python manage.py runserver 127.0.0.1:8001 --settings=config.settings.preview
```

The seed reads the reviewed files in `../catalog-work/`: `inventory-permitted.json`,
`initial-import-state.json`, `images-ready-final.json`, `category-image-plan.json`
and `category-upload-results.json`, together with their existing local image files.
When present, `public-shipping-snapshot.json` supplies reviewed delivery rules.
Use `--catalog-dir /absolute/path` if these artifacts are stored elsewhere.
It does not download anything or read credentials, production customers or orders.

Each run validates the manifests and image hashes, backs up the existing SQLite
database and media into `../catalog-work/preview-backups/`, then applies local
migrations and upserts the catalog. Repeating it does not create duplicate products,
categories or image files. Category paths are mapped to local IDs; production IDs
are only used to cross-check the source manifests. Stale local products are archived,
not deleted. Product discounts and recommendations are cleared rather than invented.

The prepared dataset has 1,233 products, 828 product photos and 41 category images.
The remaining 405 products use the site's existing missing-image treatment. The
pantry root uses the already approved basic-ingredients category illustration because
the old local category media were invalid test files. Original public product-image
attribution and license links are preserved.

Preview settings import the base settings directly, ignore all environment files,
use only `db.sqlite3` and `media/` in this checkout, and use in-memory email. Maps and
external analytics are not enabled. The seed refuses other settings modules,
non-SQLite databases, cached nonlocal connections, routers, remote/custom storage
and network email backends. The database and image storage guards run again at
the backup and seed entry points.
The public contact details come from `https://www.kodpendule.com/kontakt/` (checked
15 October 2026).

The public checkout snapshot has one active city, Vrdnik: 300 RSD same-day delivery,
free at a cart subtotal of 2,000 RSD or more, and free for a future scheduled date.
The source also stores 150 RSD as the discounted tariff, but its active mode is
`free`, so that unused value does not change the charge. The snapshot contains the
public city selector and delivery JSON, plus a hash of the public checkout script
used to verify the calculation. No other cities or delivery prices are invented.
Seeding maps cities by name to local IDs and deactivates local cities absent from
the snapshot without deleting them. Without a snapshot, existing local zones are
preserved. The seed itself never visits the live site.

The command does not create users or orders. If an admin login is needed, create a
local account with `manage.py createsuperuser --settings=config.settings.preview`.

The latest run summary is `../catalog-work/local-preview-report.json`. To restore,
stop the development server, copy the selected backup's `db.sqlite3` over the local
database and restore its `media.tar.gz` into the checkout. Preserve any later local
work before replacing those files. Backups may contain local-only data and are kept
outside the Git repository.

Validation:

```sh
.venv/bin/python manage.py test apps.core.tests.test_local_preview --settings=config.settings.preview
.venv/bin/python manage.py check --settings=config.settings.preview
```
