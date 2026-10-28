"""
Agente Auditor Grounded (Anti-Alucinaciones).
Contrasta cualquier afirmación del informe contra el contenido literal del PDF.
Si una afirmación contiene números o títulos que no están en el documento, la bloquea.
"""

import re
from pathlib import Path
from typing import Dict, List, Any
from .pdf_extractor import GroundedPDFExtractor


class AntecedenteAuditor:
    """Audita la fidelidad de una cita o antecedente contra su PDF fuente."""

    def __init__(self, pdf_dir: str):
        self.pdf_dir = Path(pdf_dir)

    def auditar_documento(self, filename: str, datos_afirmados: Dict[str, Any]) -> Dict[str, Any]:
        pdf_path = self.pdf_dir / filename
        if not pdf_path.exists():
            return {
                "archivo": filename,
                "estado": "ERROR_ARCHIVO_NO_EXISTE",
                "detalles": f"No se encontró el archivo físico en {self.pdf_dir}"
            }

        extractor = GroundedPDFExtractor(str(pdf_path))
        full_text = extractor.get_full_text()
        full_text_lower = full_text.lower()
        cover_info = extractor.extract_cover_info()

        errores = []
        advertencias = []

        # 1. Auditoría del Número de Páginas
        total_paginas = extractor.get_page_count()
        paginas_esperadas = datos_afirmados.get("paginas_esperadas")
        if paginas_esperadas is not None and total_paginas != paginas_esperadas:
            errores.append(
                f"DISCREPANCIA_PAGINAS: Se afirmaron {paginas_esperadas} páginas en la ficha, pero el PDF físico tiene exactamente {total_paginas} páginas."
            )

        # 2. Auditoría del Título
        titulo_afirmado = datos_afirmados.get("titulo", "")
        if titulo_afirmado:
            # Buscar fragmentos representativos del título
            palabras_clave_titulo = [p.lower() for p in titulo_afirmado.split() if len(p) > 4]
            coincidencias = [p for p in palabras_clave_titulo if p in full_text_lower[:5000]]
            ratio = len(coincidencias) / len(palabras_clave_titulo) if palabras_clave_titulo else 0
            if ratio < 0.5:
                errores.append(
                    f"DISCREPANCIA_TITULO: El título afirmado ('{titulo_afirmado}') no coincide con las primeras páginas del PDF. "
                    f"Texto real detectado en carátula: {' / '.join(cover_info['primeras_lineas'][:5])}"
                )

        # 3. Auditoría de Cifras, Estadísticas y Términos Clave
        full_text_normalized = re.sub(r'\s+', ' ', full_text_lower)
        cifras_afirmadas = datos_afirmados.get("cifras", [])
        for cifra in cifras_afirmadas:
            cifra_clean = re.sub(r'\s+', ' ', str(cifra).strip().lower())
            if cifra_clean not in full_text_lower and cifra_clean not in full_text_normalized:
                errores.append(
                    f"CIFRA_NO_VERIFICABLE: La cifra o término '{cifra}' fue afirmado en el informe pero NO existe en el texto del PDF."
                )

        # 4. Extraer evidencia real de Resumen y Conclusiones
        resumen_real = extractor.find_section(["RESUMEN", "ABSTRACT"], max_chars=1500)
        conclusiones_reales = extractor.find_section(["CONCLUSIONES", "CONCLUSIONS", "RESULTADOS"], max_chars=1500)

        # 4. Obtener porcentajes reales comprobados en el documento
        porcentajes_reales = extractor.find_all_percentages()[:5]

        aprobado = len(errores) == 0

        return {
            "archivo": filename,
            "estado": "VERIFICADO_CORRECTO" if aprobado else "RECHAZADO_CON_OBSERVACIONES",
            "errores_criticos": errores,
            "advertencias": advertencias,
            "paginas_totales": extractor.get_page_count(),
            "caratula_detectada": cover_info["primeras_lineas"][:8],
            "resumen_extraido": resumen_real[:500] + "..." if resumen_real else "No detectado con regex estándar",
            "conclusiones_extraidas": conclusiones_reales[:500] + "..." if conclusiones_reales else "No detectado con regex estándar",
            "porcentajes_reales_en_texto": [p["oracion_contexto"] for p in porcentajes_reales]
        }
