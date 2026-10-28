"""OCR aislado sobre una copia derivada; el PDF original nunca se modifica."""

import os
import importlib.util
import subprocess
import sys
from pathlib import Path

from thesis.services.errors import DomainError


def create_searchable_pdf(original: Path, output: Path) -> None:
    if importlib.util.find_spec("ocrmypdf") is None:
        raise DomainError("OCR_UNAVAILABLE", "OCRmyPDF no está instalado en el servidor")
    languages = os.getenv("TESISMCP_OCR_LANGUAGES", "spa+eng")
    if not languages or any(not part.isalpha() for part in languages.split("+")):
        raise DomainError("OCR_UNAVAILABLE", "TESISMCP_OCR_LANGUAGES es inválido")
    environment = os.environ.copy()
    local_tessdata = Path(__file__).resolve().parents[3] / "var" / "tessdata"
    if (local_tessdata / "spa.traineddata").is_file():
        environment.setdefault("TESSDATA_PREFIX", str(local_tessdata))
    try:
        subprocess.run(
            [sys.executable, "-m", "ocrmypdf", "--language", languages, "--output-type", "pdf", "--skip-text",
             str(original), str(output)],
            check=True, capture_output=True, text=True, timeout=300, env=environment,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        output.unlink(missing_ok=True)
        raise DomainError("OCR_FAILED", "OCRmyPDF no pudo procesar el PDF; revise idiomas y dependencias") from exc
