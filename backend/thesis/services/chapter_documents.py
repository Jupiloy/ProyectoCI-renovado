"""Edición versionada del árbol canónico de contenido por capítulo."""

import hashlib
import json
from uuid import NAMESPACE_URL, UUID, uuid5

from django.db import transaction

from thesis.models import Chapter, ChapterDocument, ChapterDocumentRevision, ChapterRevision, ResearchProfile
from thesis.services.access import require_project
from thesis.services.errors import DomainError
from thesis.services.steps import CHAPTER_STEPS
from thesis.step_catalogue import CATALOGO_PASOS
from thesis.services.citation_occurrences import list_citation_marks, normalize_citation_marks, persist_citation_marks

SCHEMA_VERSION = 2
LEGACY_SCHEMA_VERSION = 1
MAX_BLOCKS = 1000
MAX_TEXT_LENGTH = 200_000
MAX_BLOCK_TEXT = 20_000
BLOCK_FIELDS = {
    "heading": {"type", "id", "level", "text"},
    "paragraph": {"type", "id", "text"},
    "blockquote": {"type", "id", "text"},
    "code_block": {"type", "id", "text"},
    "bullet_list": {"type", "id", "items"},
    "ordered_list": {"type", "id", "items"},
    "data_table": {"type", "id", "table_version_id", "result_sha256", "caption"},
    "figure": {"type", "id", "figure_version_id", "output_sha256", "caption"},
}


def normalize_content_tree(value: dict) -> tuple[dict, str]:
    """Valida el árbol v1 y devuelve una copia normalizada junto con su Markdown determinista."""
    if not isinstance(value, dict) or set(value) != {"schema_version", "blocks"}:
        raise DomainError("VALIDATION_ERROR", "content_tree debe tener schema_version y blocks")
    schema_version = value["schema_version"]
    if type(schema_version) is not int or schema_version not in {LEGACY_SCHEMA_VERSION, SCHEMA_VERSION}:
        raise DomainError("VALIDATION_ERROR", "schema_version no está soportada")
    blocks = value["blocks"]
    if not isinstance(blocks, list) or len(blocks) > MAX_BLOCKS:
        raise DomainError("VALIDATION_ERROR", f"blocks debe ser una lista de hasta {MAX_BLOCKS} elementos")

    normalized_blocks = []
    seen_ids = set()
    total_text = 0
    markdown_blocks = []
    for block in blocks:
        if not isinstance(block, dict):
            raise DomainError("VALIDATION_ERROR", "Cada bloque debe ser un objeto JSON")
        kind = block.get("type")
        if (not isinstance(kind, str) or kind not in BLOCK_FIELDS or set(block) != BLOCK_FIELDS[kind]
                or (schema_version == LEGACY_SCHEMA_VERSION and kind in {"data_table", "figure"})):
            raise DomainError("VALIDATION_ERROR", f"Tipo o campos de bloque no admitidos por schema_version {schema_version}")
        try:
            block_id = str(UUID(block["id"]))
        except (ValueError, TypeError, AttributeError) as exc:
            raise DomainError("VALIDATION_ERROR", "Cada bloque requiere un id UUID válido") from exc
        if block_id != block["id"] or block_id in seen_ids:
            raise DomainError("VALIDATION_ERROR", "Los id de bloque deben ser UUID canónicos y únicos")
        seen_ids.add(block_id)

        normalized = {"type": kind, "id": block_id}
        if kind in {"data_table", "figure"}:
            ref_field, hash_field = (("table_version_id", "result_sha256") if kind == "data_table"
                                     else ("figure_version_id", "output_sha256"))
            try:
                artifact_id = str(UUID(block[ref_field]))
            except (ValueError, TypeError, AttributeError) as exc:
                raise DomainError("VALIDATION_ERROR", f"{ref_field} debe ser un UUID canónico") from exc
            if artifact_id != block[ref_field]:
                raise DomainError("VALIDATION_ERROR", f"{ref_field} debe ser un UUID canónico")
            digest = block[hash_field]
            if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise DomainError("VALIDATION_ERROR", f"{hash_field} debe ser SHA-256 hexadecimal minúsculo")
            caption = block["caption"]
            if not isinstance(caption, str) or not caption.strip() or len(caption.strip()) > 500:
                raise DomainError("VALIDATION_ERROR", "caption es obligatorio y admite hasta 500 caracteres")
            normalized.update({ref_field: artifact_id, hash_field: digest, "caption": caption.strip()})
            total_text += len(caption)
            markdown_blocks.append(f"[{'Tabla' if kind == 'data_table' else 'Figura'}: {caption.strip()}]")
        elif kind in {"bullet_list", "ordered_list"}:
            items = block["items"]
            if (not isinstance(items, list) or not items or len(items) > 500
                    or any(not isinstance(item, str) or not item.strip() or len(item) > MAX_BLOCK_TEXT for item in items)):
                raise DomainError("VALIDATION_ERROR", "items debe contener entre 1 y 500 textos no vacíos")
            normalized["items"] = items
            total_text += sum(len(item) for item in items)
            marker = "- " if kind == "bullet_list" else None
            markdown_blocks.append("\n".join(
                f"- {item}" if marker else f"{index}. {item}"
                for index, item in enumerate(items, start=1)
            ))
        else:
            text = block["text"]
            if not isinstance(text, str) or len(text) > MAX_BLOCK_TEXT:
                raise DomainError("VALIDATION_ERROR", "text debe ser una cadena de hasta 20000 caracteres")
            if kind != "code_block" and not text.strip():
                raise DomainError("VALIDATION_ERROR", "El texto del bloque no puede estar vacío")
            normalized["text"] = text
            total_text += len(text)
            if kind == "heading":
                level = block["level"]
                if type(level) is not int or not 1 <= level <= 6:
                    raise DomainError("VALIDATION_ERROR", "heading.level debe estar entre 1 y 6")
                normalized["level"] = level
                markdown_blocks.append(f"{'#' * level} {text}")
            elif kind == "blockquote":
                markdown_blocks.append("\n".join(f"> {line}" for line in text.splitlines()))
            elif kind == "code_block":
                markdown_blocks.append(f"```\n{text}\n```")
            else:
                markdown_blocks.append(text)
        normalized_blocks.append(normalized)

    if total_text > MAX_TEXT_LENGTH:
        raise DomainError("VALIDATION_ERROR", f"El documento supera {MAX_TEXT_LENGTH} caracteres")
    normalized_tree = {"schema_version": schema_version, "blocks": normalized_blocks}
    content_md = "\n\n".join(markdown_blocks)
    if len(content_md) > MAX_TEXT_LENGTH:
        raise DomainError("VALIDATION_ERROR", f"La proyección Markdown supera {MAX_TEXT_LENGTH} caracteres")
    return normalized_tree, content_md


def _present(document: ChapterDocument, revision: ChapterDocumentRevision, *, is_legacy=False, is_stale=False) -> dict:
    return {
        "chapter_no": document.chapter.number,
        "document_version": document.lock_version,
        "revision_id": str(revision.id) if revision else None,
        "revision_no": revision.revision_no if revision else None,
        "schema_version": revision.schema_version if revision else SCHEMA_VERSION,
        "content_tree": revision.content_tree if revision else {"schema_version": SCHEMA_VERSION, "blocks": []},
        "content_md": revision.content_md if revision else "",
        "content_sha256": revision.content_sha256 if revision else "",
        "citation_manifest_sha256": revision.citation_manifest_sha256 if revision else "",
        "citations": list_citation_marks(revision) if revision else [],
        "state_version": revision.state_version if revision else None,
        "source": revision.source if revision else None,
        "is_legacy_projection": is_legacy,
        "is_stale": is_stale,
    }


def markdown_to_blocks(content: str, stable_key: str) -> list[dict]:
    """Convierte un subconjunto Markdown a bloques v1 con IDs deterministas."""
    result = []
    paragraph_lines = []
    list_items = []
    list_kind = None
    in_code = False
    code_lines = []

    def block_id(index: int) -> str:
        return str(uuid5(NAMESPACE_URL, f"tesismcp:{stable_key}:block:{index}"))

    def flush_paragraph():
        if paragraph_lines:
            result.append({"type": "paragraph", "id": block_id(len(result)), "text": "\n".join(paragraph_lines)})
            paragraph_lines.clear()

    def flush_list():
        nonlocal list_kind
        if list_items:
            result.append({"type": list_kind, "id": block_id(len(result)), "items": list(list_items)})
            list_items.clear()
            list_kind = None

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            flush_paragraph()
            flush_list()
            if in_code:
                result.append({"type": "code_block", "id": block_id(len(result)), "text": "\n".join(code_lines)})
                code_lines.clear()
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(raw_line)
            continue
        if not line:
            flush_paragraph()
            flush_list()
            continue
        if line.startswith("#") and len(line) > 1 and line[1] == " ":
            flush_paragraph()
            flush_list()
            level = len(line) - len(line.lstrip("#"))
            if level <= 6:
                result.append({"type": "heading", "id": block_id(len(result)), "level": level,
                               "text": line[level:].strip()})
            else:
                paragraph_lines.append(line)
            continue
        if line.startswith(("- ", "* ")):
            flush_paragraph()
            if list_kind not in (None, "bullet_list"):
                flush_list()
            list_kind = "bullet_list"
            list_items.append(line[2:].strip())
            continue
        if line[:1].isdigit() and ". " in line[:5]:
            flush_paragraph()
            if list_kind not in (None, "ordered_list"):
                flush_list()
            list_kind = "ordered_list"
            list_items.append(line.split(". ", 1)[1].strip())
            continue
        if line.startswith("> "):
            flush_paragraph()
            flush_list()
            result.append({"type": "blockquote", "id": block_id(len(result)), "text": line[2:]})
            continue
        flush_list()
        paragraph_lines.append(line)
    flush_paragraph()
    flush_list()
    if in_code:
        result.append({"type": "code_block", "id": block_id(len(result)), "text": "\n".join(code_lines)})
    return result


def markdown_to_content_tree(content: str, stable_key: str) -> tuple[dict, str]:
    """Convierte Markdown textual explícito a árbol v1 y valida límites/esquema."""
    if not isinstance(content, str) or not content.strip():
        raise DomainError("VALIDATION_ERROR", "El contenido Markdown debe ser texto no vacío")
    tree = {"schema_version": LEGACY_SCHEMA_VERSION, "blocks": markdown_to_blocks(content, stable_key)}
    return normalize_content_tree(tree)


def _legacy_blocks(content: str, revision: ChapterRevision) -> list[dict]:
    """Proyecta una revisión heredada a bloques estables de solo lectura."""
    return markdown_to_blocks(content, f"legacy-revision:{revision.pk}")


def get_chapter_document(actor, project_id, chapter_no: int) -> dict:
    project = require_project(actor, project_id)
    if chapter_no not in CHAPTER_STEPS:
        raise DomainError("NOT_FOUND", "Capítulo no disponible en la plataforma")
    document = ChapterDocument.objects.filter(chapter__project=project, chapter__number=chapter_no).select_related(
        "chapter", "current_revision",
    ).first()
    if document and document.current_revision:
        current_state = ResearchProfile.objects.filter(project=project).values_list("lock_version", flat=True).first()
        revision = document.current_revision
        return _present(document, revision, is_stale=revision.state_version != current_state)

    latest_by_step = {}
    revisions = ChapterRevision.objects.filter(
        chapter__project=project, chapter__number=chapter_no, step_code__in=CHAPTER_STEPS[chapter_no],
    ).order_by("step_code", "-revision_no")
    for revision in revisions:
        latest_by_step.setdefault(revision.step_code, revision)
    blocks = []
    for step_code in CHAPTER_STEPS[chapter_no]:
        revision = latest_by_step.get(step_code)
        if revision is None:
            continue
        heading_id = str(uuid5(NAMESPACE_URL, f"tesismcp:legacy-step:{revision.pk}:heading"))
        blocks.append({"type": "heading", "id": heading_id, "level": 2,
                       "text": f"{step_code}. {CATALOGO_PASOS[step_code]['nombre']}"})
        blocks.extend(_legacy_blocks(revision.content_md, revision))
    tree = {"schema_version": SCHEMA_VERSION, "blocks": blocks}
    _, content_md = normalize_content_tree(tree)
    profile_version = ResearchProfile.objects.filter(project=project).values_list("lock_version", flat=True).first()
    return {
        "chapter_no": chapter_no,
        "document_version": document.lock_version if document else 0,
        "revision_id": None,
        "revision_no": None,
        "schema_version": SCHEMA_VERSION,
        "content_tree": tree,
        "content_md": content_md,
        "content_sha256": hashlib.sha256(content_md.encode("utf-8")).hexdigest() if content_md else "",
        "state_version": profile_version,
        "is_legacy_projection": bool(blocks),
        "is_stale": False,
    }


def _citation_identity(rows: list[dict]) -> list[dict]:
    """Compara un reintento con anclas y fuentes; ignora metadatos congelados del catálogo."""
    return [
        {
            "group_id": str(row["group_id"]),
            "block_id": str(row["block_id"]),
            "position": row["position"],
            "sources": [
                {"source_id": str(source["source_id"]), "locator": source["locator"]}
                for source in row["sources"]
            ],
        }
        for row in rows
    ]


def save_chapter_document(actor, project_id, chapter_no: int, content_tree: dict,
                          expected_version: int, idempotency_key: str, *,
                          citations: list[dict] | None = None,
                          source: str = ChapterDocumentRevision.Source.USER_EDIT) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    if chapter_no not in CHAPTER_STEPS:
        raise DomainError("NOT_FOUND", "Capítulo no disponible en la plataforma")
    if source not in ChapterDocumentRevision.Source.values:
        raise DomainError("VALIDATION_ERROR", "Origen de revisión documental no admitido")
    try:
        key = UUID(str(idempotency_key))
    except (ValueError, TypeError) as exc:
        raise DomainError("VALIDATION_ERROR", "idempotency_key debe ser UUID") from exc
    normalized_tree, content_md = normalize_content_tree(content_tree)
    from thesis.services.document_artifacts import validate_document_artifacts
    validate_document_artifacts(project, normalized_tree)
    citation_rows, citation_manifest_sha256 = normalize_citation_marks(project, normalized_tree, citations or [])
    tree_bytes = json.dumps(normalized_tree, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    content_sha256 = hashlib.sha256(tree_bytes).hexdigest()

    with transaction.atomic():
        profile = ResearchProfile.objects.select_for_update().get(project=project)
        chapter, _ = Chapter.objects.get_or_create(project=project, number=chapter_no)
        chapter = Chapter.objects.select_for_update().get(pk=chapter.pk)
        document = ChapterDocument.objects.select_for_update().filter(chapter=chapter).first()
        if document is None:
            document = ChapterDocument.objects.create(chapter=chapter, updated_by=actor)

        existing = ChapterDocumentRevision.objects.filter(document=document, idempotency_key=key).first()
        if existing:
            if (existing.content_sha256 != content_sha256 or existing.source != source
                    or _citation_identity(citation_rows) != _citation_identity(list_citation_marks(existing))):
                raise DomainError("IDEMPOTENCY_CONFLICT", "idempotency_key ya se usó con otro documento")
            return _present(document, existing, is_stale=existing.state_version != profile.lock_version) | {
                "document_version": existing.revision_no,
                "current_document_version": document.lock_version,
                "is_current": document.current_revision_id == existing.id,
                "idempotent": True,
            }

        if document.lock_version != expected_version:
            raise DomainError("VERSION_CONFLICT", "El documento cambió; carga su versión vigente antes de guardar")
        if chapter.status in (Chapter.Status.READY, Chapter.Status.APPROVED):
            raise DomainError("VERSION_CONFLICT", "El capítulo debe volver a borrador antes de editar el documento")

        if chapter.status == Chapter.Status.CHANGES_REQUESTED:
            chapter.resume_editing()
            chapter.save(update_fields=["status", "updated_at"])
        profile.lock_version += 1
        profile.save(update_fields=["lock_version", "updated_at"])
        revision_no = document.lock_version + 1
        revision = ChapterDocumentRevision.objects.create(
            document=document,
            revision_no=revision_no,
            schema_version=normalized_tree["schema_version"],
            content_tree=normalized_tree,
            content_md=content_md,
            content_sha256=content_sha256,
            citation_manifest_sha256=citation_manifest_sha256,
            state_version=profile.lock_version,
            idempotency_key=key,
            source=source,
            created_by=actor,
        )
        persist_citation_marks(revision, actor, citation_rows)
        document.current_revision = revision
        document.lock_version = revision_no
        document.updated_by = actor
        document.save(update_fields=["current_revision", "lock_version", "updated_by", "updated_at"])
    return _present(document, revision, is_stale=False) | {"idempotent": False}
