"""Preparación y comprobación de la demostración MCP local."""

from mcp_server.django_bridge import setup_django


def _preparar_usuarios_y_tokens():
    """Crea o recupera los usuarios del caso semilla UTP Sede Piura y emite sus tokens MCP."""
    setup_django()
    from asgiref.sync import sync_to_async
    from django.contrib.auth import get_user_model
    from thesis.services.mcp_auth import issue_token

    def _sync_setup():
        User = get_user_model()
        student, _ = User.objects.update_or_create(
            email="u202112345@utp.edu.pe",
            defaults={
                "display_name": "Josué Carrasco García (Tesista UTP Piura)",
                "is_active": True,
            },
        )
        advisor, _ = User.objects.update_or_create(
            email="asesor.sistemas@utp.edu.pe",
            defaults={
                "display_name": "Dr. Carlos Ramos Mendoza (Asesor UTP Piura)",
                "is_active": True,
            },
        )
        student_token = issue_token(student)
        advisor_token = issue_token(advisor)
        return student.email, advisor.email, student_token, advisor_token

    return sync_to_async(_sync_setup)()


def _registrar_antecedentes_verificados(project_id: str, pdf_filename: str = "INT1_ARIA_Multi_LLM_Framework_2025.pdf"):
    """Registra un PDF real descargado con páginas físicas extraídas y extractos en PostgreSQL."""
    setup_django()
    import hashlib
    import uuid
    from pathlib import Path
    from asgiref.sync import sync_to_async
    from django.conf import settings
    from thesis.integrations.pdf import extract_pages
    from thesis.models import Project, SourceDocument, SourceExcerpt

    def _sync_register():
        project = Project.objects.get(id=project_id)
        pdf_path = Path("docs/antecedentes_descargados") / pdf_filename
        if not pdf_path.is_file():
            raise FileNotFoundError(f"No se encontró el PDF real en {pdf_path}")

        pdf_bytes = pdf_path.read_bytes()
        digest = hashlib.sha256(pdf_bytes).hexdigest()
        count, pages = extract_pages(pdf_path)

        source_id = uuid.uuid4()
        media_root = Path(settings.MEDIA_ROOT).resolve()
        dest_dir = media_root / "sources" / str(project.id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / f"{source_id}.pdf"
        dest_file.write_bytes(pdf_bytes)
        storage_key = str(dest_file.relative_to(media_root))

        source = SourceDocument.objects.create(
            id=source_id,
            project=project,
            kind=SourceDocument.Kind.UPLOAD,
            title="Accelerating Scientific Research Through a Multi-LLM Framework",
            authors_json=["Joaquin Ramirez-Medina", "Mohammadmehdi Ataei", "Alidad Amirfazli"],
            publication_year=2025,
            doi="10.48550/arXiv.2502.07960",
            storage_key=storage_key,
            sha256=digest,
            mime_type="application/pdf",
            page_count=count,
            verification_status=SourceDocument.Status.TEXT_CHECKED,
            extraction_method=SourceDocument.ExtractionMethod.POPPLER,
        )

        chunks = []
        for page_no, page_text in pages:
            for offset in range(0, len(page_text), 4000):
                content = page_text[offset : offset + 4000].strip()
                if content:
                    chunks.append(
                        SourceExcerpt(
                            source=source,
                            chunk_no=len(chunks) + 1,
                            page_no=page_no,
                            text=content,
                            text_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                        )
                    )
        SourceExcerpt.objects.bulk_create(chunks)

        first_chunk = SourceExcerpt.objects.filter(source=source, page_no=1).first()
        return {
            "source_id": str(source.id),
            "source_sha256": source.sha256,
            "page_count": source.page_count,
            "title": source.title,
            "doi": source.doi,
            "first_excerpt_id": first_chunk.id if first_chunk else None,
            "total_excerpts": len(chunks),
        }

    return sync_to_async(_sync_register)()


def _inspeccionar_bd_relacional(project_id: str) -> dict:
    """Consulta en PostgreSQL el conteo exacto de entidades relacionales generadas por el flujo MCP."""
    setup_django()
    from asgiref.sync import sync_to_async
    from thesis.models import (
        Chapter,
        ChapterRevision,
        ConsistencyRow,
        ConsistencyRowVariable,
        Indicator,
        Instrument,
        InstrumentItem,
        InstrumentItemIndicator,
        ResearchProfile,
        ResearchVariable,
        ReviewComment,
        ReviewEvent,
        SourceDocument,
        StepProgress,
        VariableDimension,
    )

    def _sync_counts():
        profile = ResearchProfile.objects.get(project_id=project_id)
        return {
            "lock_version": profile.lock_version,
            "ods_code": profile.ods_code,
            "approach": profile.approach,
            "steps_completed": StepProgress.objects.filter(project_id=project_id, status="COMPLETED").count(),
            "chapters_approved": Chapter.objects.filter(project_id=project_id, status=Chapter.Status.APPROVED).count(),
            "chapter_revisions": ChapterRevision.objects.filter(chapter__project_id=project_id).count(),
            "consistency_rows": ConsistencyRow.objects.filter(project_id=project_id).count(),
            "consistency_row_vars": ConsistencyRowVariable.objects.filter(consistency_row__project_id=project_id).count(),
            "research_variables": ResearchVariable.objects.filter(project_id=project_id).count(),
            "variable_dimensions": VariableDimension.objects.filter(variable__project_id=project_id).count(),
            "indicators": Indicator.objects.filter(dimension__variable__project_id=project_id).count(),
            "verified_sources": SourceDocument.objects.filter(project_id=project_id).count(),
            "instruments": Instrument.objects.filter(project_id=project_id).count(),
            "instrument_items": InstrumentItem.objects.filter(instrument__project_id=project_id).count(),
            "item_indicator_links": InstrumentItemIndicator.objects.filter(
                instrument_item__instrument__project_id=project_id
            ).count(),
            "review_comments_resolved": ReviewComment.objects.filter(
                revision__chapter__project_id=project_id, status=ReviewComment.Status.RESOLVED
            ).count(),
            "review_events": ReviewEvent.objects.filter(revision__chapter__project_id=project_id).count(),
        }

    return sync_to_async(_sync_counts)()
