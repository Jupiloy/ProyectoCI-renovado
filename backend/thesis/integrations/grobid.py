"""Cliente local de GROBID; el TEI resultante es extracción automática."""

import os
from urllib.parse import urlparse

import requests
from defusedxml import ElementTree as ET

from thesis.services.errors import DomainError


TEI = "{http://www.tei-c.org/ns/1.0}"
MAX_TEI_BYTES = 20 * 1024 * 1024


def _base_url() -> str:
    url = os.getenv("TESISMCP_GROBID_URL", "http://127.0.0.1:8070").rstrip("/")
    parsed = urlparse(url)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "grobid"} or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path:
        raise DomainError("GROBID_UNAVAILABLE", "GROBID debe configurarse como servicio HTTP local")
    return url


def process_fulltext(pdf_path) -> bytes:
    try:
        with open(pdf_path, "rb") as pdf:
            with requests.post(
                f"{_base_url()}/api/processFulltextDocument",
                files={"input": ("source.pdf", pdf, "application/pdf")},
                data={"consolidateHeader": "0", "consolidateCitations": "0"},
                headers={"Accept": "application/xml"}, timeout=(5, 120), stream=True,
            ) as response:
                response.raise_for_status()
                chunks, size = [], 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > MAX_TEI_BYTES:
                        raise DomainError("GROBID_FAILED", "El TEI de GROBID excede el límite local")
                    chunks.append(chunk)
                result = b"".join(chunks)
                if not result:
                    raise DomainError("GROBID_FAILED", "GROBID devolvió una respuesta vacía")
                return result
    except (requests.RequestException, OSError) as exc:
        raise DomainError("GROBID_UNAVAILABLE", "No se pudo procesar el PDF con GROBID local") from exc


def _text(element) -> str:
    return " ".join(" ".join(element.itertext()).split()) if element is not None else ""


def _authors(parent) -> list[str]:
    names = []
    for author in parent.findall(TEI + "author"):
        person = author.find(TEI + "persName")
        names.append(_text(person if person is not None else author))
    return [name for name in names if name]


def parse_tei(content: bytes) -> dict:
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise DomainError("GROBID_FAILED", "GROBID no devolvió TEI XML válido") from exc
    if root.tag != TEI + "TEI":
        raise DomainError("GROBID_FAILED", "GROBID no devolvió un documento TEI")
    header = root.find(f"{TEI}teiHeader/{TEI}fileDesc/{TEI}titleStmt")
    analytic_header = root.find(f"{TEI}teiHeader/{TEI}fileDesc/{TEI}sourceDesc/{TEI}biblStruct/{TEI}analytic")
    title = _text(header.find(TEI + "title")) if header is not None else ""
    if not title and analytic_header is not None:
        title = _text(analytic_header.find(TEI + "title"))
    authors = _authors(analytic_header) if analytic_header is not None else []
    if not authors and header is not None:
        authors = _authors(header)
    references = []
    for item in root.findall(f".//{TEI}listBibl/{TEI}biblStruct")[:500]:
        analytic = item.find(TEI + "analytic")
        monogr = item.find(TEI + "monogr")
        source = analytic if analytic is not None else monogr
        ref_title = _text(source.find(TEI + "title")) if source is not None else ""
        if not ref_title and monogr is not None:
            ref_title = _text(monogr.find(TEI + "title"))
        ref_authors = _authors(source) if source is not None else []
        doi = next((_text(node) for node in item.findall(f".//{TEI}idno") if node.get("type", "").lower() == "doi"), None)
        references.append({
            "tei_id": item.get("{http://www.w3.org/XML/1998/namespace}id"),
            "title": ref_title, "authors": ref_authors, "doi": doi,
            "raw_text": _text(item)[:2000], "verified_against_original": False,
        })
    return {"title": title, "authors": authors, "references": references}
