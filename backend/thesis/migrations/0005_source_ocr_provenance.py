from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("thesis", "0004_remove_sourcedocument_source_project_openalex_unique_and_more")]

    operations = [
        migrations.AddField(
            model_name="sourcedocument", name="derived_storage_key",
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name="sourcedocument", name="derived_sha256",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name="sourcedocument", name="extraction_method",
            field=models.CharField(blank=True, choices=[("POPPLER", "Texto del PDF original"), ("OCR", "Texto de copia procesada por OCR")], max_length=10, null=True),
        ),
    ]
