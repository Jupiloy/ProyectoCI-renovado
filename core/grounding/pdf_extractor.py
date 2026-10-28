"""
Módulo de Extracción y Auditoría Grounded de Documentos Científicos.
Diseñado para el protocolo TesisMCP para erradicar alucinaciones bibliográficas.
Extrae metadatos reales, resúmenes, conclusiones y verifica números en PDFs locales.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any


class GroundedPDFExtractor:
    """Extrae texto verificado directamente desde archivos PDF usando herramientas del sistema."""

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo: {pdf_path}")
        self._raw_text: Optional[str] = None
        self._page_count: Optional[int] = None

    def get_page_count(self) -> int:
        if self._page_count is not None:
            return self._page_count
        try:
            res = subprocess.run(["pdfinfo", str(self.pdf_path)], capture_output=True, text=True, check=True)
            for line in res.stdout.splitlines():
                if line.startswith("Pages:"):
                    self._page_count = int(line.split(":")[1].strip())
                    return self._page_count
        except Exception:
            pass
        # Fallback usando pdftotext
        text = self.get_full_text()
        self._page_count = text.count("\x0c") or 1
        return self._page_count

    def extract_pages(self, start_page: int, end_page: int) -> str:
        """Extrae un rango específico de páginas (1-indexed)."""
        cmd = ["pdftotext", "-f", str(start_page), "-l", str(end_page), str(self.pdf_path), "-"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout

    def get_full_text(self) -> str:
        if self._raw_text is None:
            cmd = ["pdftotext", str(self.pdf_path), "-"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self._raw_text = res.stdout
        return self._raw_text

    def extract_cover_info(self) -> Dict[str, Any]:
        """Extrae el texto de las primeras 3 páginas para detectar título real, autores e institución."""
        first_pages = self.extract_pages(1, min(3, self.get_page_count()))
        lines = [line.strip() for line in first_pages.splitlines() if line.strip()]
        
        # Buscar Universidad / Institución
        institution = "Desconocida"
        for line in lines[:15]:
            if any(k in line.upper() for k in ["UNIVERSIDAD", "UNIVERSITY", "INSTITUTO", "FACULTAD"]):
                institution = line
                break

        return {
            "archivo": self.pdf_path.name,
            "primeras_lineas": lines[:25],
            "institucion_probable": institution
        }

    def find_section(self, section_names: List[str], max_chars: int = 3000) -> Optional[str]:
        """Busca una sección específica en el texto completo y extrae su contenido."""
        full_text = self.get_full_text()
        
        for name in section_names:
            # Buscar encabezado de sección aislado
            pattern = rf"(?:\n|\r|\f)\s*(?:[0-9IVX\.\s]{{0,6}})?({name})\b[:\s]*\n"
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                start_pos = match.end()
                content = full_text[start_pos : start_pos + max_chars].strip()
                # Cortar en el siguiente salto de sección mayor o página
                page_break = content.find("\x0c")
                if page_break != -1 and page_break > 200:
                    content = content[:page_break].strip()
                return content
        return None

    def find_all_percentages(self) -> List[Dict[str, str]]:
        """Extrae todas las oraciones que contienen porcentajes reales en el texto."""
        full_text = self.get_full_text()
        # Normalizar espacios
        cleaned = re.sub(r"\s+", " ", full_text)
        # Buscar oraciones con porcentajes
        pattern = r"([^.?!]{10,120}\b\d+(?:\.\d+)?\s*(?:%|por ciento)\b[^.?!]{10,120}[.?!])"
        matches = re.findall(pattern, cleaned, re.IGNORECASE)
        
        results = []
        for m in matches:
            sentence = m.strip()
            # Extraer el número específico
            num_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|por ciento)", sentence)
            if num_match:
                results.append({
                    "cifra": num_match.group(1) + "%",
                    "oracion_contexto": sentence
                })
        return results

    def verify_claim(self, claim: str) -> Dict[str, Any]:
        """Verifica si una afirmación o cifra específica existe textualmente en el PDF."""
        full_text = self.get_full_text().lower()
        claim_clean = claim.lower().strip()
        
        # Buscar números específicos en la afirmación
        numbers = re.findall(r"\b\d+(?:\.\d+)?%?", claim_clean)
        missing_numbers = [n for n in numbers if n not in full_text]
        
        exact_match = claim_clean in full_text
        
        # Búsqueda difusa de palabras clave principales
        words = [w for w in re.findall(r"\b\w{5,}\b", claim_clean) if w not in ["sobre", "para", "mediante", "donde", "entre"]]
        found_words = [w for w in words if w in full_text]
        word_coverage = len(found_words) / len(words) if words else 0.0

        return {
            "afirmacion_evaluada": claim,
            "coincidencia_exacta": exact_match,
            "numeros_no_encontrados": missing_numbers,
            "cobertura_palabras_clave": f"{word_coverage:.1%}",
            "es_veridica": exact_match or (len(missing_numbers) == 0 and word_coverage > 0.6)
        }
