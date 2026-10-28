"""Parseres deliberadamente acotados para exportaciones bibliográficas aportadas por usuarios."""

import csv
import io
import re
import unicodedata
from typing import Any

from thesis.services.errors import DomainError


MAX_IMPORT_BYTES = 5 * 1024 * 1024
MAX_IMPORT_RECORDS = 500
MAX_FIELD_LENGTH = 20_000
SUPPORTED_FORMATS = {"ris", "bib", "bibtex", "csv"}


def _clean(value: Any, max_length: int = MAX_FIELD_LENGTH) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\x00", "").split())[:max_length]


def _normalize_record(record: dict[str, Any]) -> dict[str, Any] | None:
    title = _clean(record.get("title"))
    if not title:
        return None
    authors = record.get("authors") or []
    if isinstance(authors, str):
        authors = re.split(r"\s+and\s+|\s*;\s*", authors, flags=re.IGNORECASE)
    authors = [_clean(author, 500) for author in authors if _clean(author, 500)]
    year_raw = _clean(record.get("year"), 10)
    year_match = re.search(r"\b(\d{4})\b", year_raw)
    year = int(year_match.group(1)) if year_match else None
    if year is not None and not 1000 <= year <= 9999:
        year = None
    doi = _clean(record.get("doi"), 255)
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE).rstrip(".,; ") or None
    url = _clean(record.get("url"), 2048)
    if url and not re.match(r"^https?://", url, flags=re.IGNORECASE):
        url = ""
    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": doi,
        "url": url or None,
        "abstract": _clean(record.get("abstract")),
        "venue": _clean(record.get("venue"), 2000),
        "record_id": _clean(record.get("record_id"), 512) or None,
    }


def _split_ris(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    record: dict[str, Any] = {"authors": []}
    last_key: str | None = None

    def finish() -> None:
        nonlocal record
        if record:
            rows.append(record)
        record = {"authors": []}

    for line in text.splitlines():
        match = re.match(r"^([A-Z0-9]{2})\s+-\s+(.*)$", line)
        if not match:
            if line[:1].isspace() and last_key and record.get(last_key):
                old = record[last_key]
                if isinstance(old, list):
                    old[-1] = f"{old[-1]} {line.strip()}"
                else:
                    record[last_key] = f"{old} {line.strip()}"
            continue
        tag, value = match.groups()
        value = value.strip()
        if tag == "TY" and record.get("title"):
            finish()
        if tag == "ER":
            finish()
            last_key = None
            continue
        mapping = {
            "TI": "title", "T1": "title", "CT": "title", "AU": "authors", "A1": "authors",
            "PY": "year", "Y1": "year", "DO": "doi", "UR": "url", "AB": "abstract",
            "N2": "abstract", "JO": "venue", "JF": "venue", "T2": "venue", "ID": "record_id",
            "AN": "record_id", "DB": "venue",
        }
        key = mapping.get(tag)
        if key:
            if key == "authors":
                record["authors"].append(value)
            elif key in ("title", "abstract", "venue") and key in record and value:
                record[key] = f"{record[key]} {value}"
            else:
                record[key] = value
            last_key = key
        else:
            last_key = None
    finish()
    return rows


def _read_braced_value(text: str, pos: int) -> tuple[str, int]:
    if pos >= len(text):
        return "", pos
    if text[pos] == "{":
        depth, start, pos = 1, pos + 1, pos + 1
        while pos < len(text) and depth:
            if text[pos] == "{":
                depth += 1
            elif text[pos] == "}":
                depth -= 1
            pos += 1
        return text[start:pos - 1], pos
    if text[pos] == '"':
        start, pos = pos + 1, pos + 1
        escaped = False
        while pos < len(text):
            char = text[pos]
            if char == '"' and not escaped:
                return text[start:pos], pos + 1
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
            pos += 1
        return text[start:], pos
    start = pos
    while pos < len(text) and text[pos] not in ",}\n":
        pos += 1
    return text[start:pos].strip(), pos


def _split_bibtex(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pos = 0
    while True:
        start = text.find("@", pos)
        if start < 0:
            break
        head = re.match(r"@([A-Za-z]+)\s*([{(])", text[start:])
        if not head:
            pos = start + 1
            continue
        kind, opening = head.group(1).lower(), head.group(2)
        body_start = start + head.end()
        closing = "}" if opening == "{" else ")"
        depth, quoted, escaped, end = 1, False, False, body_start
        while end < len(text) and depth:
            char = text[end]
            if char == '"' and not escaped:
                quoted = not quoted
            elif not quoted:
                if char == opening:
                    depth += 1
                elif char == closing:
                    depth -= 1
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
            end += 1
        pos = end
        if kind in {"comment", "preamble", "string"}:
            continue
        body = text[body_start:end - 1]
        comma = body.find(",")
        if comma < 0:
            continue
        key = body[:comma].strip()
        fields_text = body[comma + 1:]
        fields: dict[str, str] = {}
        cursor = 0
        while cursor < len(fields_text):
            while cursor < len(fields_text) and fields_text[cursor] in " \t\r\n,":
                cursor += 1
            match = re.match(r"([A-Za-z][A-Za-z0-9_-]*)\s*=\s*", fields_text[cursor:])
            if not match:
                cursor += 1
                continue
            field = match.group(1).lower()
            cursor += match.end()
            pieces = []
            value, cursor = _read_braced_value(fields_text, cursor)
            pieces.append(value)
            while cursor < len(fields_text) and fields_text[cursor] == "#":
                value, cursor = _read_braced_value(fields_text, cursor + 1)
                pieces.append(value)
            fields[field] = "".join(pieces)
            while cursor < len(fields_text) and fields_text[cursor] not in ",":
                cursor += 1
        author_text = fields.get("author", "")
        plain = lambda value: re.sub(r"[{}]", "", value or "")
        rows.append({
            "title": plain(fields.get("title")),
            "authors": re.split(r"\s+and\s+", plain(author_text), flags=re.IGNORECASE) if author_text else [],
            "year": plain(fields.get("year")), "doi": plain(fields.get("doi")), "url": plain(fields.get("url")),
            "abstract": plain(fields.get("abstract")), "venue": plain(fields.get("journal") or fields.get("booktitle")),
            "record_id": key,
        })
    return rows


def _split_csv(text: str) -> list[dict[str, Any]]:
    try:
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise DomainError("VALIDATION_ERROR", "El CSV debe incluir una fila de encabezados")
        aliases = {
            "title": {"title", "titulo", "document title", "articletitle"},
            "authors": {"authors", "author", "autores", "autor"},
            "year": {"year", "publication year", "año", "ano", "date"},
            "doi": {"doi", "digital object identifier"},
            "url": {"url", "link", "record url", "web of science accession number url"},
            "abstract": {"abstract", "resumen"},
            "venue": {"journal", "source title", "publication name", "revista", "venue"},
            "record_id": {"record id", "accession number", "eid", "document id", "id"},
        }

        def key_normalize(value: str) -> str:
            value = unicodedata.normalize("NFKD", value.lower()).encode("ascii", "ignore").decode("ascii")
            return re.sub(r"[^a-z0-9]+", " ", value).strip()

        mapping = {}
        for header in reader.fieldnames:
            normalized = key_normalize(header or "")
            for field, names in aliases.items():
                if normalized in {key_normalize(name) for name in names}:
                    mapping[header] = field
                    break
        if "title" not in mapping.values():
            raise DomainError("VALIDATION_ERROR", "El CSV necesita una columna title o titulo")
        rows = []
        for raw in reader:
            row = {target: raw.get(header) for header, target in mapping.items()}
            if row.get("authors"):
                row["authors"] = re.split(r"\s*;\s*|\s+and\s+", row["authors"], flags=re.IGNORECASE)
            rows.append(row)
        return rows
    except csv.Error as exc:
        raise DomainError("VALIDATION_ERROR", "El CSV no tiene formato válido") from exc


def parse_bibliography(content: bytes, file_format: str) -> list[dict[str, Any]]:
    """Parsea RIS, BibTeX o CSV y retorna solo registros con título, sin certificar sus metadatos."""
    file_format = file_format.lower().lstrip(".")
    if file_format not in SUPPORTED_FORMATS:
        raise DomainError("VALIDATION_ERROR", "Formato no admitido; use RIS, BibTeX o CSV")
    if not content or len(content) > MAX_IMPORT_BYTES:
        raise DomainError("VALIDATION_ERROR", "El archivo debe pesar entre 1 byte y 5 MiB")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DomainError("VALIDATION_ERROR", "El archivo debe estar codificado como UTF-8") from exc
    raw_rows = _split_ris(text) if file_format == "ris" else _split_bibtex(text) if file_format in {"bib", "bibtex"} else _split_csv(text)
    if len(raw_rows) > MAX_IMPORT_RECORDS:
        raise DomainError("VALIDATION_ERROR", f"El archivo supera el máximo de {MAX_IMPORT_RECORDS} registros")
    return [row for raw in raw_rows if (row := _normalize_record(raw))]
