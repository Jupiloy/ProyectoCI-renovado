"""Conversión DOCX y lectura conservadora de campos de cita OOXML."""

import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

from thesis.services.errors import DomainError


MAX_DOCX_BYTES = 20 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_PART_BYTES = 25 * 1024 * 1024
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
PARTS = ("word/document.xml", "word/footnotes.xml", "word/endnotes.xml")


def _citation(code: str, display: str, part: str, paragraph: int) -> dict | None:
    code = code.strip()
    if re.match(r"^CITATION\s", code, re.I):
        return {"kind": "WORD", "part_name": part, "paragraph_index": paragraph,
                "display_text": display, "field_code": code[:10000], "citation_items": []}
    if not re.match(r"^ADDIN\s+ZOTERO_ITEM\s+CSL_CITATION\b", code, re.I):
        return None
    items = []
    start = code.find("{")
    if start >= 0:
        try:
            data, _ = json.JSONDecoder().raw_decode(code[start:])
            if isinstance(data, dict) and isinstance(data.get("citationItems"), list):
                items = [
                    {key: item[key] for key in ("id", "locator", "label", "prefix", "suffix") if key in item}
                    for item in data["citationItems"] if isinstance(item, dict)
                ]
        except (ValueError, TypeError):
            pass
    return {"kind": "ZOTERO", "part_name": part, "paragraph_index": paragraph,
            "display_text": display, "field_code": code[:10000], "citation_items": items}


def _text(node) -> str:
    return "".join(element.text or "" for element in node.iter(W + "t"))


def _paragraph_citations(paragraph, part: str, index: int) -> list[dict]:
    found = []
    # Complex fields have begin/instruction/separate/result/end. Preserve their displayed text.
    stack = []
    for element in paragraph.iter():
        if element.tag == W + "fldSimple":
            citation = _citation(element.get(W + "instr", ""), _text(element), part, index)
            if citation:
                found.append(citation)
        elif element.tag == W + "fldChar":
            field_type = element.get(W + "fldCharType")
            if field_type == "begin":
                stack.append({"code": "", "display": "", "result": False})
            elif field_type == "separate" and stack:
                stack[-1]["result"] = True
            elif field_type == "end" and stack:
                field = stack.pop()
                citation = _citation(field["code"], field["display"], part, index)
                if citation:
                    found.append(citation)
        elif element.tag == W + "instrText" and stack:
            stack[-1]["code"] += element.text or ""
        elif element.tag == W + "t" and stack and stack[-1]["result"]:
            stack[-1]["display"] += element.text or ""
    return found


def inspect_docx(path: Path) -> list[dict]:
    try:
        with ZipFile(path) as archive:
            names = {entry.filename: entry for entry in archive.infolist()}
            if "word/document.xml" not in names or "[Content_Types].xml" not in names:
                raise DomainError("DOCX_UNREADABLE", "El archivo no contiene un documento Word OOXML")
            if (len(names) > 3000 or sum(entry.file_size for entry in names.values()) > MAX_UNCOMPRESSED_BYTES
                    or any(entry.file_size > MAX_PART_BYTES for entry in names.values())):
                raise DomainError("DOCX_UNREADABLE", "El DOCX excede los límites de descompresión")
            citations = []
            for part in PARTS:
                if part not in names:
                    continue
                root = ET.fromstring(archive.read(part))
                for index, paragraph in enumerate(root.iter(W + "p"), start=1):
                    citations.extend(_paragraph_citations(paragraph, part, index))
            return citations
    except (BadZipFile, ET.ParseError, OSError, RuntimeError) as exc:
        raise DomainError("DOCX_UNREADABLE", "No se pudo leer la estructura DOCX") from exc


def convert_docx(path: Path) -> str:
    try:
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import DocumentConverter

        document = DocumentConverter(allowed_formats=[InputFormat.DOCX]).convert(path).document
        markdown = document.export_to_markdown()
        if not markdown.strip():
            raise ValueError("Documento sin texto convertible")
        return markdown
    except (ImportError, ModuleNotFoundError) as exc:
        # La lectura del manuscrito no debe quedar bloqueada si la instalación
        # slim de Docling carece de su extra Office. Usa el extractor estructural
        # ligero ya requerido por el proyecto y marca imágenes sin simular OCR.
        try:
            return _convert_docx_python(path)
        except Exception as fallback_exc:
            raise DomainError("DOCX_UNAVAILABLE", "No hay un extractor DOCX funcional") from fallback_exc
    except Exception as exc:
        raise DomainError("DOCX_UNREADABLE", "Docling no pudo convertir el DOCX") from exc


def _convert_docx_python(path: Path) -> str:
    """Proyección Markdown conservadora de párrafos/tablas con python-docx."""
    from docx import Document

    document = Document(path)
    blocks = []
    for item in document.iter_inner_content():
        if item.__class__.__name__ == "Paragraph":
            text = item.text.strip()
            style_name = item.style.name if item.style else ""
            if text:
                if style_name == "Title":
                    text = f"# {text}"
                elif style_name.startswith("Heading ") and style_name.split()[-1].isdigit():
                    level = min(6, int(style_name.split()[-1]))
                    text = f"{'#' * level} {text}"
                elif style_name.startswith("List Bullet"):
                    text = f"- {text}"
                elif style_name.startswith("List Number"):
                    text = f"1. {text}"
                blocks.append(text)
            image_nodes = item._p.xpath(".//wp:docPr")
            for image in image_nodes:
                label = image.get("name", "Imagen incorporada").replace("[", "(").replace("]", ")")
                blocks.append(f"[Imagen incorporada: {label}; texto de imagen no extraído]")
        else:
            rows = []
            for row in item.rows:
                cells = [cell.text.strip().replace("|", "\\|").replace("\n", "<br>") for cell in row.cells]
                rows.append("| " + " | ".join(cells) + " |")
            if rows:
                separator = "| " + " | ".join("---" for _ in item.rows[0].cells) + " |"
                rows.insert(1, separator)
                blocks.append("\n".join(rows))
    markdown = "\n\n".join(block for block in blocks if block.strip())
    if not markdown.strip():
        raise DomainError("DOCX_UNREADABLE", "El documento no contiene texto o tablas convertibles")
    return markdown
