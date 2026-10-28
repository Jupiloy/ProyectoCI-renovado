"""Plantillas de prompts para el Capítulo 4: Revisión de Literatura y Antecedentes (P13 a P20)."""

CHAPTER_4_TEMPLATES = {
    "P13": {
        "step_code": "P13",
        "prompt_name": "paso_p13_ecuaciones_busqueda",
        "titulo": "P13: Ecuaciones de Búsqueda Académica",
        "descripcion": "Diseña ecuaciones booleanas (AND, OR, NOT) con descriptores en español e inglés para Scopus e IEEE.",
        "guia_metodologica": """
Estrategia de búsqueda bibliográfica:
1. Diseña ecuaciones booleanas avanzadas combinando operadores AND, OR y comodines comillas.
2. Genera la ecuación para Scopus y para IEEE Xplore.
3. Lista entre 2 y 10 palabras clave en español y entre 2 y 10 en inglés.
""",
        "esquema_json_ejemplo": {
            "ecuacion_scopus": 'TITLE-ABS-KEY(("Model Context Protocol" OR "MCP") AND ("thesis" OR "academic writing") AND ("consistency" OR "hallucination"))',
            "ecuacion_ieee": '("Model Context Protocol" OR "MCP") AND ("academic writing" OR "thesis formulation") AND ("multi-agent")',
            "palabras_clave_es": ["Protocolo MCP", "asistencia de tesis", "consistencia metodológica", "mitigación de alucinaciones"],
            "palabras_clave_en": ["Model Context Protocol", "thesis formulation", "methodological consistency", "hallucination mitigation"]
        }
    },
    "P14": {
        "step_code": "P14",
        "prompt_name": "paso_p14_criterios_inclusion_exclusion",
        "titulo": "P14: Criterios de Inclusión y Exclusión de Literatura",
        "descripcion": "Establece criterios de cribado, rango temporal (últimos 5 años) e idiomas admitidos.",
        "guia_metodologica": """
Delimitación de la revisión sistemática:
1. Criterios de inclusión: entre 2 y 6 reglas claras (ej. artículos de revistas indexadas Scopus/WoS, tesis de posgrado/pregrado con metodología explícita).
2. Criterios de exclusión: entre 2 y 6 causales (ej. resúmenes de congresos sin texto completo, artículos de opinión, herramientas comerciales sin evaluación empírica).
3. Rango temporal: anio_inicio (>= 2018) y anio_fin (<= 2026), donde anio_inicio <= anio_fin.
4. Idiomas admitidos: lista de códigos o nombres de idiomas (ej. ["Español", "Inglés"]).
""",
        "esquema_json_ejemplo": {
            "criterios_inclusion": [
                "Artículos en revistas o conferencias indexadas en Scopus, IEEE Xplore o Web of Science",
                "Tesis universitarias con pruebas preexperimentales o cuasiexperimentales y muestra verificable",
                "Estudios publicados entre 2018 y 2026 orientados a arquitecturas de software o IA educativa"
            ],
            "criterios_exclusion": [
                "Publicaciones de divulgación o blogs sin revisión por pares ciegos",
                "Documentos cuyo texto completo físico no esté disponible para auditoría",
                "Sistemas propietarios sin métricas empíricas de evaluación demostradas"
            ],
            "anio_inicio": 2020,
            "anio_fin": 2026,
            "idiomas_admitidos": ["Español", "Inglés"]
        }
    },
    "P15": {
        "step_code": "P15",
        "prompt_name": "paso_p15_protocolo_prisma",
        "titulo": "P15: Protocolo de Cribado PRISMA",
        "descripcion": "Estructura el embudo de selección PRISMA con métricas estrictamente decrecientes o iguales.",
        "guia_metodologica": """
Embudo de cribado sistemático PRISMA:
1. El flujo debe cumplir la invariante matemática decreciente o igual:
   registros_identificados >= registros_cribados >= articulos_evaluados_texto_completo >= estudios_incluidos.
2. Registra los duplicados removidos.
3. Todas las métricas deben ser números enteros positivos congruentes con las búsquedas reales.
""",
        "esquema_json_ejemplo": {
            "registros_identificados": 45,
            "registros_duplicados_removidos": 5,
            "registros_cribados": 40,
            "articulos_evaluados_texto_completo": 15,
            "estudios_incluidos": 7
        }
    },
    "P16": {
        "step_code": "P16",
        "prompt_name": "paso_p16_matriz_literatura",
        "titulo": "P16: Matriz de Literatura Científica (Grounded Truth)",
        "descripcion": "Sintetiza los antecedentes con anclaje de evidencia obligatoria a extractos de PDFs verificados.",
        "guia_metodologica": """
🛡️ REGLA DE ORO GROUNDED TRUTH (ANTI-ALUCINACIONES):
1. El backend BLOQUEARÁ cualquier estudio cuyo PDF no esté registrado en SourceDocument con extractos físicos.
2. Cada estudio requiere: autores, año (2018-2026), título exacto de la portada, metodología, muestra y hallazgo principal.
3. Obligatorio anclar pasajes verificados con su excerpt_id real:
   - metodologia_evidencia: { excerpt_id: int, cita_textual: str }
   - muestra_evidencia: { excerpt_id: int, cita_textual: str }
   - hallazgo_evidencia: { excerpt_id: int, cita_textual: str }
4. Usa `consultar_extractos` o `localizar_frase` sobre una fuente incorporada para obtener los `excerpt_id` reales. La búsqueda de antecedentes devuelve solo metadatos.
5. El JSON siguiente ilustra la estructura. Sustituye los ID y coteja cada afirmación con el PDF; la coincidencia literal no acredita por sí sola el significado de una conclusión.
""",
        "esquema_json_ejemplo": {
            "estudios": [
                {
                    "autores": "Joaquin Ramirez-Medina, Mohammadmehdi Ataei, Alidad Amirfazli",
                    "anio": 2025,
                    "titulo": "Accelerating Scientific Research Through a Multi-LLM Framework",
                    "metodologia": "Marco ARIA de cuatro agentes y varios modelos de lenguaje",
                    "muestra": "Caso de estudio sobre mejora de la condensación por gotas",
                    "hallazgo_principal": "En el caso descrito, ARIA realizó tareas de investigación en aproximadamente una hora con supervisión humana.",
                    "doi": "10.48550/arXiv.2502.07960",
                    "verification_level": "TEXT_EXTRACTED_WITH_QUOTES",
                    "paginas_reales": 34,
                    "metodologia_evidencia": {
                        "excerpt_id": 1,
                        "cita_textual": "Artificial Research Innovator Assistant\n(ARIA), a four-agent, multi-LLM framework."
                    },
                    "muestra_evidencia": {
                        "excerpt_id": 1,
                        "cita_textual": "In a case study on dropwise condensation enhancement,\nARIA demonstrates its capability to streamline research tasks within an hour"
                    },
                    "hallazgo_evidencia": {
                        "excerpt_id": 1,
                        "cita_textual": "streamline research tasks within an hour, maintaining\nuser oversight during execution and ultimately liberating researchers from time-intensive\ntasks."
                    }
                }
            ]
        }
    },
    "P17": {
        "step_code": "P17",
        "prompt_name": "paso_p17_sintesis_tematica",
        "titulo": "P17: Síntesis Temática y Patrones de la Literatura",
        "descripcion": "Identifica ejes temáticos, consensos y discrepancias metodológicas en los antecedentes analizados.",
        "guia_metodologica": """
Análisis comparativo de antecedentes:
1. Ejes temáticos: entre 2 y 6 líneas de análisis transversal (ej. arquitecturas de agentes, mitigación de alucinaciones).
2. Consensos de la literatura: entre 1 y 6 puntos donde los autores coinciden empíricamente.
3. Discrepancias o debates: entre 1 y 6 tensiones o limitaciones encontradas en los estudios previos.
""",
        "esquema_json_ejemplo": {
            "ejes_tematicos": [
                "Efectividad de arquitecturas multi-agente vs. LLM único monolítico",
                "Sistemas web de gestión de tesis y su impacto en tiempos de tramitación",
                "Estrategias deterministas para prevención de alucinaciones bibliográficas"
            ],
            "consensos_literatura": [
                "Registrar aquí únicamente coincidencias respaldadas por los antecedentes incluidos y sus páginas físicas",
                "Separar los resultados observados de las capacidades que los autores solo propusieron"
            ],
            "discrepancias_o_debates": [
                "Debate entre el uso de modelos locales ligeros con menor latencia frente a APIs comerciales más costosas"
            ]
        }
    },
    "P18": {
        "step_code": "P18",
        "prompt_name": "paso_p18_brecha_investigacion",
        "titulo": "P18: Brecha y Agenda de Investigación",
        "descripcion": "Argumenta el vacío empírico identificado en la literatura y la justificación de la necesidad del estudio.",
        "guia_metodologica": """
Fundamentación de la brecha:
1. Vacío de conocimiento identificado: explica qué aspecto metodológico o técnico no ha sido resuelto por los antecedentes (30 a 500 caracteres).
2. Justificación de la necesidad del estudio: sustenta por qué es indispensable construir la solución propuesta (30 a 500 caracteres).
""",
        "esquema_json_ejemplo": {
            "vacio_conocimiento_identificado": "En los antecedentes seleccionados para este proyecto todavía no se ha documentado la combinación específica de búsqueda, validación por etapas y revisión docente.",
            "justificacion_necesidad_estudio": "Es necesario dotar a los estudiantes de herramientas que garanticen la integridad metodológica y trazabilidad de fuentes antes de presentar sus planes de tesis a los jurados."
        }
    },
    "P19": {
        "step_code": "P19",
        "prompt_name": "paso_p19_redaccion_marco_antecedentes",
        "titulo": "P19: Redacción del Marco de Antecedentes",
        "descripcion": "Redacta los antecedentes internacionales, nacionales y la síntesis comparativa en prosa formal.",
        "guia_metodologica": """
Estructura de la redacción de antecedentes:
1. Antecedentes internacionales: redacción académica detallada de al menos 100 caracteres con autores, año, muestra y aportes foráneos.
2. Antecedentes nacionales: redacción académica de al menos 100 caracteres integrando estudios peruanos de universidades licenciadas.
3. Síntesis comparativa: párrafo conclusivo de al menos 50 caracteres que articule los antecedentes con la tesis actual.
""",
        "esquema_json_ejemplo": {
            "antecedentes_internacionales": "Ramirez-Medina, Ataei y Amirfazli (2025) describen ARIA, un marco de cuatro agentes. En un caso sobre condensación por gotas, informan que realizó tareas de investigación en aproximadamente una hora con supervisión humana; no es una medida general de mejora de tesis.",
            "antecedentes_nacionales": "Para cada antecedente nacional seleccionado, completar el autor, año, diseño, población y resultado únicamente después de inspeccionar el documento completo y localizar la página física correspondiente.",
            "sintesis_comparativa": "Comparar las funciones documentadas de los estudios incluidos sin convertir las propuestas técnicas en resultados empíricos demostrados."
        }
    },
    "P20": {
        "step_code": "P20",
        "prompt_name": "paso_p20_referencias_apa7",
        "titulo": "P20: Referencias Bibliográficas Normalizadas (IEEE)",
        "instrucciones_base": "Propón referencias en IEEE para el piloto. Usa solo fuentes identificadas, coteja los metadatos y señala los datos faltantes. La corrección del formato y el respaldo de las citas requieren revisión humana.",
        "descripcion": "Propone referencias en IEEE para el piloto; conserva APA 7 para compatibilidad con trabajos anteriores.",
        "guia_metodologica": """
Normalización de referencias:
1. Para el piloto usa estilo_citacion 'IEEE'; 'APA_7' permanece admitido para trabajos anteriores.
2. Cada referencia debe incluir autor(es), año, título, fuente y DOI o URL oficial cuando exista; coteja estos datos con la portada y el registro.
3. Incluye entre 1 y 50 referencias. La estructura no garantiza corrección IEEE: revisa cada tipo documental y su fuente.
""",
        "esquema_json_ejemplo": {
            "estilo_citacion": "IEEE",
            "referencias_formateadas": [
                "J. Ramirez-Medina, M. Ataei y A. Amirfazli, \"Accelerating Scientific Research Through a Multi-LLM Framework,\" 2025, doi: 10.48550/arXiv.2502.07960."
            ]
        }
    }
}
