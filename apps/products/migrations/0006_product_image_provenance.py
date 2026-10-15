from django.core.validators import URLValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("products", "0005_product_barcode_xmlimportbatch")]

    operations = [
        migrations.AddField(
            model_name="product", name="is_archived",
            field=models.BooleanField(default=False, db_index=True, verbose_name="Archived", help_text="Archived products are hidden from the shop and cannot be purchased. Clear this option to restore them."),
        ),
        migrations.AddField(
            model_name="product", name="main_image_source_url",
            field=models.URLField(blank=True, max_length=1000, validators=[URLValidator(schemes=["http", "https"])], verbose_name="Image source URL"),
        ),
        migrations.AddField(
            model_name="product", name="main_image_attribution",
            field=models.CharField(blank=True, max_length=255, verbose_name="Image attribution"),
        ),
        migrations.AddField(
            model_name="product", name="main_image_license_url",
            field=models.URLField(blank=True, max_length=1000, validators=[URLValidator(schemes=["http", "https"])], verbose_name="Image license URL"),
        ),
    ]
