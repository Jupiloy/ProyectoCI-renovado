"""Descarga controlada y extracción física de páginas de PDF públicos."""

import hashlib
import ipaddress
import re
import socket
import subprocess
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from thesis.services.errors import DomainError

MAX_PDF_BYTES = 30 * 1024 * 1024
MAX_PAGES = 300


def _public_https(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise DomainError("PDF_UNAVAILABLE", "El enlace PDF debe ser HTTPS público")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise DomainError("PDF_UNAVAILABLE", "No se pudo resolver el servidor del PDF") from exc
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise DomainError("PDF_UNAVAILABLE", "El enlace PDF no apunta a una dirección pública")


class PublicRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        _public_https(newurl)
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def download_pdf(url: str, destination: Path) -> str:
    """Devuelve SHA-256; no conserva un archivo parcial ante un fallo."""
    _public_https(url)
    opener = build_opener(ProxyHandler({}), PublicRedirects())
    digest = hashlib.sha256()
    size = 0
    try:
        with opener.open(Request(url, headers={"User-Agent": "TesisMCP/0.1", "Accept": "application/pdf"}), timeout=20) as response:
            content_type = response.headers.get_content_type()
            if content_type not in {"application/pdf", "application/octet-stream"}:
                raise DomainError("PDF_UNAVAILABLE", "El enlace no devolvió un PDF")
            with destination.open("wb") as output:
                while chunk := response.read(65536):
                    size += len(chunk)
                    if size > MAX_PDF_BYTES:
                        raise DomainError("PDF_UNAVAILABLE", "El PDF supera el límite local de descarga")
                    output.write(chunk)
                    digest.update(chunk)
        with destination.open("rb") as downloaded:
            header = downloaded.read(5)
        if size == 0 or header != b"%PDF-":
            raise DomainError("PDF_UNAVAILABLE", "El archivo recibido no tiene cabecera PDF")
        return digest.hexdigest()
    except DomainError:
        destination.unlink(missing_ok=True)
        raise
    except (OSError, TimeoutError, ValueError, HTTPError, URLError) as exc:
        destination.unlink(missing_ok=True)
        raise DomainError("PDF_UNAVAILABLE", "No se pudo descargar el PDF") from exc


def extract_pages(path: Path) -> tuple[int, list[tuple[int, str]]]:
    try:
        info = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, check=True, timeout=20)
        match = re.search(r"^Pages:\s+(\d+)\s*$", info.stdout, re.MULTILINE)
        if not match:
            raise DomainError("PDF_UNREADABLE", "pdfinfo no informó el número físico de páginas")
        count = int(match.group(1))
        if not 1 <= count <= MAX_PAGES:
            raise DomainError("PDF_UNREADABLE", "El número de páginas excede el límite local")
        pages = []
        for number in range(1, count + 1):
            result = subprocess.run(
                ["pdftotext", "-f", str(number), "-l", str(number), "-enc", "UTF-8", str(path), "-"],
                capture_output=True, text=True, check=True, timeout=20,
            )
            page_text = result.stdout.replace("\f", "").strip()
            if page_text:
                pages.append((number, page_text))
        return count, pages
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired, UnicodeError) as exc:
        raise DomainError("PDF_UNREADABLE", "No se pudo extraer el texto físico del PDF") from exc
