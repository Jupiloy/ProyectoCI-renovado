"""Embeddings multilingües locales; FastEmbed solo descarga el modelo al prepararlo."""

from functools import lru_cache
from pathlib import Path

from django.conf import settings

from thesis.services.errors import DomainError


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
VECTOR_DIMENSIONS = 384


@lru_cache(maxsize=1)
def _model():
    try:
        from fastembed import TextEmbedding

        cache = Path(settings.MEDIA_ROOT).parent / "models" / "fastembed"
        cache.mkdir(parents=True, exist_ok=True)
        return TextEmbedding(model_name=MODEL_NAME, cache_dir=str(cache), threads=2)
    except Exception as exc:
        raise DomainError("EMBEDDING_UNAVAILABLE", "No se pudo cargar el modelo multilingüe local") from exc


def embed_texts(texts: list[str]) -> list[list[float]]:
    try:
        vectors = [vector.tolist() for vector in _model().embed(texts, batch_size=16)]
    except DomainError:
        raise
    except Exception as exc:
        raise DomainError("EMBEDDING_UNAVAILABLE", "No se pudieron generar vectores locales") from exc
    if len(vectors) != len(texts) or any(len(vector) != VECTOR_DIMENSIONS for vector in vectors):
        raise DomainError("EMBEDDING_UNAVAILABLE", "El modelo devolvió vectores de tamaño inesperado")
    return vectors
