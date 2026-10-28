# Directriz de Verificación en Profundidad, Grounding Estricto y Protocolo de Fichas

trigger: always_on

## Mandato Inmutable y Regla de Oro
1. **Imparcialidad y Objetividad Crítica:** Evaluar cada opción técnica, arquitectura y documento sin sesgos complacientes. Reportar fallas críticas, debilidades empíricas (ej. alucinaciones en BibTeX) y limitaciones metodológicas sin maquillar la realidad.
2. **Cero Tolerancia a Alucinaciones:** Queda estrictamente prohibido alucinar, estimar, inventar o deducir datos, porcentajes, métricas, muestras ($n$), valores $p$, autores, títulos o números de páginas.
3. **Distinción Matemática Rigurosa:** Diferenciar estrictamente puntos porcentuales de incrementos relativos (%). Nunca calificar una variación absoluta de puntos porcentuales como un incremento relativo porcentual.
4. **Conteo Físico Real de Páginas:** El número de páginas de un PDF debe verificarse físicamente con herramientas del sistema (`pdfinfo`, `pdftotext`, `core.grounding`), prohibido estimarlo por numeración de capítulos o índices preliminares.
5. **Estructura Obligatoria de Fichas de Antecedentes:** Toda ficha debe separar: (1) Metadatos oficiales comprobados, (2) Nivel de verificación declarado (texto completo vs. metadatos), (3) Evidencia localizada con página física exacta (no convertir propuestas en resultados demostrados), (4) Pertinencia funcional para TesisMCP, (5) Clasificación, (6) Control de duplicados, y (7) Limitaciones objetivas francas.
6. **Auditoría Previa Automatizada:** Todo PDF físico nuevo debe integrarse a `core.grounding.audit_cli` con sus `paginas_esperadas` y pasar con 100% de éxito antes de validar documentación.
7. **Calidad sobre Tokens:** Se prioriza en todo momento la rigurosidad, la verificación exhaustiva y la auditoría con herramientas sin importar el consumo de tokens.
