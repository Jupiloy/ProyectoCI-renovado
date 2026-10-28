"""Coincidencias probables por DOI/título; nunca fusiona registros."""

import re
import unicodedata

from thesis.models import SourceDocument


def title_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", (value or "").casefold()).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def duplicate_match(left: SourceDocument, right: SourceDocument) -> str | None:
    """Devuelve el indicio compartido; no declara que dos registros sean la misma obra."""
    if (left.record_provider == right.record_provider
            and left.provider_record_id == right.provider_record_id):
        return None
    normalized_doi = (left.doi or "").casefold()
    same_doi = bool(normalized_doi and right.doi and normalized_doi == right.doi.casefold())
    normalized_title = title_key(left.title)
    same_title = bool(normalized_title and normalized_title == title_key(right.title))
    if same_doi and same_title:
        return "DOI_AND_TITLE"
    if same_doi:
        return "DOI"
    if same_title:
        return "TITLE"
    return None


def candidate_duplicates(project, *, title: str, doi: str | None, record_provider: str,
                         provider_record_id: str) -> list[dict]:
    query = SourceDocument.objects.filter(project=project, kind=SourceDocument.Kind.EXTERNAL)
    candidates = []
    probe = SourceDocument(title=title, doi=doi, record_provider=record_provider,
                           provider_record_id=provider_record_id)
    for source in query.only("id", "title", "doi", "record_provider", "provider_record_id"):
        match = duplicate_match(probe, source)
        if match:
            candidates.append({
                "source_id": str(source.id),
                "match": match,
                "title": source.title,
                "provider": source.record_provider,
                "provider_record_id": source.provider_record_id,
            })
            if len(candidates) == 10:
                break
    return candidates
