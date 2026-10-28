"""La etiqueta anterior de P16 exageraba el alcance de la extracción automática."""

from django.db import migrations
from django.core.exceptions import ValidationError


def relabel_p16(apps, schema_editor):
    StepProgress = apps.get_model("thesis", "StepProgress")
    SourceDocument = apps.get_model("thesis", "SourceDocument")
    SourceExcerpt = apps.get_model("thesis", "SourceExcerpt")

    def has_extracted_quotes(progress, study):
        try:
            source = SourceDocument.objects.filter(
                id=study.get("source_id"), project_id=progress.project_id,
                verification_status="TEXT_CHECKED",
            ).first()
        except (TypeError, ValueError, ValidationError):
            return False
        if not source or not source.page_count or not source.storage_key or not source.sha256:
            return False
        for field in ("metodologia_evidencia", "muestra_evidencia", "hallazgo_evidencia"):
            evidence = study.get(field)
            if not isinstance(evidence, dict):
                return False
            quote = evidence.get("cita_textual")
            excerpt_id = evidence.get("excerpt_id")
            try:
                excerpt = SourceExcerpt.objects.filter(id=excerpt_id, source=source).first() if excerpt_id else None
            except (TypeError, ValueError, ValidationError):
                return False
            if not quote or not excerpt or quote not in excerpt.text:
                return False
        return True

    for progress in StepProgress.objects.filter(step_code="P16").iterator():
        output = progress.output_json or {}
        if not isinstance(output, dict):
            continue
        changed = False
        studies = output.get("estudios")
        if not isinstance(studies, list):
            continue
        for study in studies:
            if isinstance(study, dict) and study.get("verification_level") == "FULL_TEXT_INSPECTED":
                study["verification_level"] = (
                    "TEXT_EXTRACTED_WITH_QUOTES" if has_extracted_quotes(progress, study)
                    else "LEGACY_UNVERIFIED"
                )
                changed = True
        if changed:
            progress.output_json = output
            progress.save(update_fields=["output_json"])


class Migration(migrations.Migration):
    dependencies = [
        ("thesis", "0017_instruments_and_items"),
    ]

    operations = [
        migrations.RunPython(relabel_p16, migrations.RunPython.noop),
    ]
