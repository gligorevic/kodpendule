from django.db import migrations


def update_working_hours(apps, schema_editor):
    translations = apps.get_model("core", "FooterSettingsTranslation")
    for language, hours in (
        ("sr", "Svakog dana: 07:00–24:00"),
        ("en", "Every day: 07:00–24:00"),
    ):
        translations.objects.using(schema_editor.connection.alias).filter(
            master_id=1, language_code=language
        ).update(working_hours=hours)


class Migration(migrations.Migration):
    dependencies = [("core", "0004_remove_checkoutsettings")]
    operations = [migrations.RunPython(update_working_hours, migrations.RunPython.noop)]
