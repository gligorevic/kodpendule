import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0004_productimage_bilingual_alt_text"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="barcode",
            field=models.CharField(blank=True, db_index=True, max_length=64, verbose_name="Barcode"),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.UniqueConstraint(condition=~models.Q(barcode=""), fields=("barcode",), name="products_unique_nonempty_barcode"),
        ),
        migrations.CreateModel(
            name="XMLImportBatch",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("filename", models.CharField(max_length=255)),
                ("file_sha256", models.CharField(db_index=True, max_length=64)),
                ("payload", models.JSONField(default=dict)),
                ("categories", models.JSONField(default=dict)),
                ("result", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("applied_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
