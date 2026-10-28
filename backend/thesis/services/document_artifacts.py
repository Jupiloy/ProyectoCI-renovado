"""Validación y resolución exacta de artefactos referenciados por capítulos."""

import hashlib
import json
from pathlib import Path
from uuid import UUID

from django.conf import settings

from thesis.models import ResearchFigureVersion, ResearchTableRecipeVersion
from thesis.services.errors import DomainError


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _hash(value):
    return hashlib.sha256(value).hexdigest()


def validate_document_artifacts(project, content_tree):
    """Exige que cada referencia exista en el proyecto y coincidan hashes y archivo físico."""
    manifest = []
    for block in content_tree.get("blocks", []):
        if block["type"] == "data_table":
            version = ResearchTableRecipeVersion.objects.filter(
                pk=block["table_version_id"], recipe__dataset_version__dataset__project=project,
            ).select_related("recipe").first()
            if version is None:
                raise DomainError("ARTIFACT_NOT_FOUND", "La versión de tabla no pertenece a este proyecto")
            if _hash(_canonical(version.result_json)) != version.result_sha256 or version.result_sha256 != block["result_sha256"]:
                raise DomainError("ARTIFACT_HASH_MISMATCH", "El resultado de tabla no coincide con el hash del bloque")
            manifest.append({"block_id": block["id"], "type": "data_table", "artifact_version_id": str(version.id),
                             "artifact_sha256": version.result_sha256, "caption": block["caption"],
                             "source_result_sha256": version.expected_input_sha256})
        elif block["type"] == "figure":
            version = ResearchFigureVersion.objects.filter(
                pk=block["figure_version_id"], figure__table_version__recipe__dataset_version__dataset__project=project,
            ).select_related("figure").first()
            if version is None:
                raise DomainError("ARTIFACT_NOT_FOUND", "La versión de figura no pertenece a este proyecto")
            if version.output_sha256 != block["output_sha256"]:
                raise DomainError("ARTIFACT_HASH_MISMATCH", "El hash de la figura no coincide con el bloque")
            root = Path(settings.MEDIA_ROOT).resolve()
            path = (root / version.storage_key).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                raise DomainError("ARTIFACT_UNAVAILABLE", "El PNG de la figura no está disponible")
            payload = path.read_bytes()
            if len(payload) != version.size_bytes or _hash(payload) != version.output_sha256:
                raise DomainError("ARTIFACT_HASH_MISMATCH", "El PNG no coincide con la versión inmutable")
            manifest.append({"block_id": block["id"], "type": "figure", "artifact_version_id": str(version.id),
                             "artifact_sha256": version.output_sha256, "caption": block["caption"],
                             "accessibility": version.accessibility_json, "width": version.width,
                             "height": version.height, "mime_type": version.mime_type,
                             "renderer_version": version.renderer_version,
                             "source_result_sha256": version.source_result_sha256})
    return manifest


def verify_snapshot_artifacts(snapshot):
    """Revalida los bytes/versiones exactos del snapshot antes de entregar un export."""
    manifest = snapshot.document_artifacts_manifest
    if not isinstance(manifest, list):
        raise DomainError("ARTIFACT_MANIFEST_INVALID", "El manifest de artefactos del snapshot no es una lista")
    revision = snapshot.document_revision
    blocks = {block["id"]: block for block in (revision.content_tree.get("blocks", []) if revision else [])}
    expected = []
    for block in blocks.values():
        if block["type"] in {"data_table", "figure"}:
            expected.append(block["id"])
    if sorted(expected) != sorted(item.get("block_id") for item in manifest):
        raise DomainError("ARTIFACT_MANIFEST_INVALID", "El manifest no cubre exactamente los bloques de artefacto")
    verified = []
    for item in manifest:
        block = blocks.get(item.get("block_id"))
        if block is None or item.get("type") != block["type"]:
            raise DomainError("ARTIFACT_MANIFEST_INVALID", "El tipo o bloque del manifest no coincide")
        if block["type"] == "data_table":
            version = ResearchTableRecipeVersion.objects.filter(
                pk=item.get("artifact_version_id"),
                recipe__dataset_version__dataset__project_id=snapshot.chapter.project_id,
            ).first()
            if (version is None or str(version.id) != block["table_version_id"]
                    or version.result_sha256 != block["result_sha256"]
                    or item.get("artifact_sha256") != version.result_sha256
                    or item.get("caption") != block["caption"]
                    or _hash(_canonical(version.result_json)) != version.result_sha256):
                raise DomainError("ARTIFACT_HASH_MISMATCH", "La tabla congelada del snapshot falta o no coincide")
            verified.append({**item, "result": version.result_json})
        else:
            version = ResearchFigureVersion.objects.filter(
                pk=item.get("artifact_version_id"),
                figure__table_version__recipe__dataset_version__dataset__project_id=snapshot.chapter.project_id,
            ).first()
            if (version is None or str(version.id) != block["figure_version_id"]
                    or version.output_sha256 != block["output_sha256"]
                    or item.get("artifact_sha256") != version.output_sha256
                    or item.get("caption") != block["caption"]
                    or item.get("accessibility") != version.accessibility_json
                    or item.get("width") != version.width or item.get("height") != version.height
                    or item.get("mime_type") != version.mime_type
                    or item.get("renderer_version") != version.renderer_version):
                raise DomainError("ARTIFACT_HASH_MISMATCH", "La figura congelada del snapshot falta o no coincide")
            root = Path(settings.MEDIA_ROOT).resolve()
            path = (root / version.storage_key).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                raise DomainError("ARTIFACT_UNAVAILABLE", "El PNG congelado del snapshot no está disponible")
            data = path.read_bytes()
            if len(data) != version.size_bytes or _hash(data) != version.output_sha256:
                raise DomainError("ARTIFACT_HASH_MISMATCH", "Los bytes de figura del snapshot no coinciden")
            verified.append({**item, "path": path})
    return {item["block_id"]: item for item in verified}
