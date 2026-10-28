#!/usr/bin/env python3
"""Benchmark local, reproducible y no destructivo del corpus multiformato B7.

Uso: python scripts/benchmark_multiformat.py /ruta/al/corpus --output /tmp/b7.json
No sube archivos ni interpreta corrección científica. Los originales no se modifican.
"""

import argparse
import hashlib
import json
import mimetypes
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_DEBUG", "1")
import django  # noqa: E402
django.setup()

from thesis.integrations.pdf import extract_pages  # noqa: E402
from thesis.integrations.multiformat import extract_office  # noqa: E402
from thesis.services.errors import DomainError  # noqa: E402


SUPPORTED = {".pdf", ".docx", ".pptx", ".xlsx"}


def inspect_file(path: Path) -> dict:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    started = time.perf_counter()
    details: dict = {}
    status = "OK"
    try:
        if path.suffix.lower() == ".pdf":
            page_count, pages = extract_pages(path)
            details = {
                "physical_pages": page_count,
                "pages_with_extractable_digital_text": len(pages),
                "pages_without_extractable_digital_text": max(0, page_count - len(pages)),
                "text_characters": sum(len(text) for _, text in pages),
                "selective_ocr_indicated": len(pages) < page_count,
                "locator_level": "physical_page",
                "extractor": "Poppler pdfinfo+pdftotext",
                "ocr_executed": False,
            }
        else:
            segments, metadata = extract_office(path, path.suffix.lower())
            details = {
                **metadata,
                "text_segments": sum(bool(item["text"].strip()) for item in segments),
                "text_characters": sum(len(item["text"]) for item in segments),
                "image_references": sum(item["kind"] == "IMAGE_REFERENCE" for item in segments),
                "locators_sample": [item["locator_json"] for item in segments[:10]],
            }
    except (DomainError, OSError, ValueError) as exc:
        status = "FAILED"
        details = {"error_code": getattr(exc, "code", "LOCAL_IO_ERROR"), "error": str(exc)}
    return {
        "filename": path.name,
        "extension": path.suffix.lower(),
        "mime_type_guess": mimetypes.guess_type(path.name)[0],
        "size_bytes": path.stat().st_size,
        "sha256": digest,
        "status": status,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "details": details,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path, help="Directorio con documentos de evaluación")
    parser.add_argument("--output", type=Path, required=True, help="Ruta donde guardar JSON del benchmark")
    args = parser.parse_args()
    corpus = args.corpus.expanduser().resolve()
    if not corpus.is_dir():
        parser.error("corpus debe ser un directorio local existente")
    files = sorted(path for path in corpus.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED)
    report = {
        "benchmark": "TesisMCP B7 local multiformat",
        "corpus_path": str(corpus),
        "files_total": len(files),
        "scope": "Extracción estructural/recuento; sin evaluación de veracidad científica",
        "files": [inspect_file(path) for path in files],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failures = sum(item["status"] != "OK" for item in report["files"])
    print(json.dumps({"files_total": len(files), "failures": failures, "report": str(args.output)}))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
