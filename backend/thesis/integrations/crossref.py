"""Lectura de metadatos DOI del registro Crossref."""

import os
import re
from urllib.parse import quote

import requests

from thesis.services.errors import DomainError


DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$", re.IGNORECASE)


def get_doi_record(doi: str) -> dict:
    doi = doi.strip().removeprefix("https://doi.org/").removeprefix("http://doi.org/")
    if not DOI_PATTERN.fullmatch(doi) or len(doi) > 255:
        raise DomainError("VALIDATION_ERROR", "DOI inválido")
    email = os.getenv("OPENALEX_CONTACT_EMAIL", "").strip()
    agent = "TesisMCP/0.1"
    if email:
        agent += f" (mailto:{email})"
    try:
        response = requests.get(f"https://api.crossref.org/works/{quote(doi, safe='/')}",
                                headers={"User-Agent": agent}, timeout=15)
        if response.status_code == 404:
            raise DomainError("NOT_FOUND", "DOI no encontrado en Crossref")
        response.raise_for_status()
        payload = response.json()
    except DomainError:
        raise
    except (requests.RequestException, ValueError) as exc:
        raise DomainError("REGISTRY_UNAVAILABLE", "No se pudo consultar Crossref") from exc
    message = payload.get("message")
    if not isinstance(message, dict) or not message.get("DOI"):
        raise DomainError("REGISTRY_UNAVAILABLE", "Crossref devolvió una respuesta inválida")
    return message
