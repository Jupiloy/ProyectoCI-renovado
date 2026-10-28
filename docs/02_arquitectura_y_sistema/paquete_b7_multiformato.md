# B7 — Ingesta y búsqueda de documentos multiformato

**Estado de implementación:** implementado y verificado por puerta integral el 26/10/2026.  
**Base física verificada:** 52 modelos y 40 migraciones (`0001`–`0040`).  
**Propósito:** permitir que el tesista incorpore PDF, DOCX, PPTX y XLSX al corpus del proyecto, conservar el original y recuperar texto con referencias navegables propias de cada formato.

## 1. Resultado esperado

1. El titular carga un documento mediante el endpoint de fuentes existente. El backend conserva el nombre de archivo base (sin rutas), valida extensión/cabecera, aplica el límite local de 30 MiB, calcula SHA-256, conserva el original bajo almacenamiento del proyecto y encola el extractor adecuado.
2. Los trabajos se ejecutan en el worker documental existente; no se añade una cola ni un agente alternativo. Los errores quedan visibles en `DocumentJob` y `SourceDocument.extraction_state`.
3. El extractor persiste unidades estructurales en `SourceSegment`. Cada unidad tiene tipo, orden, texto/hash, método/versión y `locator_json` con coordenadas del archivo original.
4. La búsqueda/indexación semántica acepta tanto los `SourceExcerpt` PDF legados como los nuevos segmentos. Devuelve pasaje candidato, fuente, ID de segmento y localizador. Un candidato recuperado no es una cita confirmada ni valida la afirmación.
5. `SourceExcerpt.page_no` y `EvidenceLink` permanecen intactos para evidencia PDF que ya usa el flujo de citas. No se simula una página para diapositivas u hojas de cálculo.

## 2. Formatos y localizadores

| Formato | Extractor | Unidades y localizadores | Límites explícitos |
|---|---|---|---|
| PDF digital | Poppler (`pdfinfo`, `pdftotext`) | `SourceExcerpt` con página física; búsqueda mantiene página exacta. | Máximo local 30 MiB y 300 páginas en la extracción existente. No se infieren datos bibliográficos de la portada. |
| PDF escaneado o mixto | OCRmyPDF + Tesseract, con `--skip-text` | Se marcan páginas sin texto digital; OCR se ejecuta solo en páginas que el motor aún no puede leer, preservando páginas digitales. La copia OCR tiene hash separado; el original no se cambia. | Si siguen faltando páginas con texto después del OCR, estado `PARTIAL` y no se afirma extracción integral. Las páginas realmente en blanco pueden seguir sin texto. |
| DOCX | `python-docx` | Párrafo/estilo; filas de tabla con tabla, fila y celdas; referencia de imagen dentro del párrafo cuando se detecta. | No interpreta imágenes, comentarios, cambios controlados ni campos como evidencia académica. Las referencias de imagen no se someten a OCR en B7. |
| PPTX | `python-pptx` | Diapositiva/forma; filas de tablas; nombres de forma; referencia de imagen por diapositiva/forma. | No se extraen notas del presentador ni texto dentro de imágenes. Orden nativo de diapositiva/forma se conserva en secuencia. |
| XLSX | `openpyxl` | Hoja, fila, rango/celda; cada celda conserva `value_or_formula`, bandera `is_formula` y valor almacenado en caché si existe. | No se evalúan ni recalculan fórmulas. El valor cacheado puede faltar o estar desactualizado. Gráficos/formato visual no se reconstruyen como datos. Imagen anclada se registra como referencia, sin OCR. |

Los formatos Office se validan como paquetes OOXML ZIP, con límites de cantidad de miembros, tamaño expandido, tamaño por miembro y razón de compresión. El parser solo admite los tipos OOXML indicados; un ZIP arbitrario o dañado se marca fallido.

## 3. Estados y afirmaciones

`SourceDocument.extraction_state` distingue `NOT_STARTED`, `QUEUED`, `EXTRACTED`, `OCR_REQUIRED`, `PARTIAL`, `NO_TEXT` y `FAILED`. El campo no sustituye `verification_status`: texto extraído significa contenido disponible/localizable, no metadatos bibliográficos verificados, pertinencia, revisión por pares, corrección de fórmulas ni respaldo semántico de una afirmación.

Los registros incluyen hash de entrada, preservación del original, parser y versión, cantidades estructurales y flags de capacidad. Cada segmento posee SHA-256 sobre su texto extraído (vacío en referencias visuales) y datos JSON de ubicación/metadatos. La extracción se rehace reemplazando segmentos únicamente para un trabajo pendiente de extracción; las referencias históricas del PDF continúan usando el esquema existente.

## 4. Contrato API

- `POST /api/v1/projects/{project_id}/sources/upload`: multipart `label` + `file`; ahora admite `.pdf`, `.docx`, `.pptx`, `.xlsx`; devuelve `202` cuando el trabajo queda en cola. Solo titular carga.
- `GET /api/v1/projects/{project_id}/sources/{source_id}/segments?offset=0&limit=50`: lectura paginada (límite 100) de segmentos/localizadores. Requiere acceso al proyecto y fuente del mismo proyecto.
- `POST /api/v1/projects/{project_id}/sources/{source_id}/index`: indexa extractos PDF y segmentos con texto mediante el modelo embedding ya configurado.
- `POST /api/v1/projects/{project_id}/passages/search`: devuelve candidatos con `physical_page` solamente para PDF; para Office entrega `segment_id`, `locator` y `locator_kind`.
- `GET /api/v1/projects/{project_id}/jobs/{job_id}`: expone estado/resultado/error del trabajo conforme al contrato de jobs existente.

El upload conserva la ruta y nombre histórico para el PDF; `upload_pdf_pending` se mantiene como wrapper de compatibilidad del servicio. El trabajo PDF sigue siendo `PDF_EXTRACT`; Office usa `FORMAT_EXTRACT`. La API de manuscritos DOCX sigue siendo separada: un borrador del tesista no se transforma en fuente de investigación.

**Compatibilidad DOCX del manuscrito:** `convert_docx` usa Docling cuando su importación/extra Office está disponible; si el paquete slim no ofrece ese import, usa `python-docx` para proyectar párrafos, títulos, listas y tablas. Esta ruta no procesa texto dentro de imágenes y deja un marcador explícito. Fallos reales durante una conversión de Docling instalada siguen siendo errores visibles; no se ocultan tras el fallback.

## 5. Modelos y migraciones

- `SourceSegment`: fuente, secuencia única, tipo, localizador JSON, texto/hash, método/versión y metadatos estructurales.
- `SourcePassage`: admite exactamente uno de `excerpt` o `segment`, con restricción de base de datos. `excerpt` sigue resolviendo citas PDF históricas; `segment` permite retrieval no paginado.
- `SourceDocument`: nombre original base, estados/detalles de extracción, opciones de extracción estructural y método multiformato.
- `DocumentJob.Kind.FORMAT_EXTRACT`: trabajo de Office en cola documental actual.
- `0038_multiformat_source_segments.py`, `0039_multiformat_extraction_states.py` y `0040_source_original_filename.py`: migraciones aditivas; las filas de pasajes legados mantienen `excerpt` y `segment=NULL`.

El conteo esperado del modelo de dominio pasa de 51 a 52 modelos; migraciones de 37 a 40. El verificador de proyecto debe reflejar estos conteos basándose en el código real.

## 6. Evaluación reproducible

`backend/thesis/tests/test_multiformat_sources.py` genera documentos de prueba deterministas durante la ejecución para DOCX (párrafo + tabla), PPTX (diapositiva + tabla) y XLSX (hoja + valores + fórmula). Las pruebas verifican carga, hash/original, job, extracción, localizadores, búsqueda candidata, metadatos de fórmula sin recálculo, manejo OOXML inválido y permisos.

El comando `python scripts/benchmark_multiformat.py /ruta/al/corpus --output /tmp/b7.json` evalúa un corpus local elegido por el equipo y guarda nombre, extensión, MIME inferido, tamaño/hash, tiempo, versiones del parser, cantidad de páginas/segmentos, localizadores de ejemplo, fórmulas e imágenes. En PDF cuenta páginas físicas y páginas con texto digital; indica si se requiere OCR, pero no ejecuta OCR automáticamente. Los tiempos describen solo esa máquina y ese corpus. No se incluye ni redistribuye material protegido; las pruebas sintéticas no sustituyen una evaluación representativa de PDFs escaneados/mixtos reales.

No se publican cifras de rendimiento ni precisión OCR hasta ejecutar el benchmark con un conjunto representativo, autorizado y reportar su composición.

### Protocolo pendiente para calidad de extracción/OCR

1. Construir un corpus local de uso autorizado que cubra PDF digital, escaneado y mixto, además de DOCX, PPTX y XLSX. Registrar cantidad real por formato, idioma, tamaño, páginas/hojas y presencia de tablas, fórmulas e imágenes; no fijar una muestra antes de conocer el material disponible.
2. Para cada archivo, producir una referencia manual revisada: texto seleccionado, página física o localizador de Office, orden de lectura, filas/celdas de tablas y elementos que el extractor debe marcar como imagen/no textual. En OCR, conservar la transcripción de referencia de páginas seleccionadas.
3. Ejecutar el benchmark de metadatos y extracción; para OCR registrar aparte si la página requería OCR, si se procesó, si conservó el número de páginas y el texto resultante. Comparar la salida con la referencia: exactitud de localizador, cobertura de contenido, errores de caracteres/palabras para OCR y preservación de estructura tabular. Reportar fallos por archivo, no ocultarlos en un promedio.
4. Registrar motor/versión/configuración, equipo, tiempo, memoria, idioma OCR, hash del original y hash del derivado. Separar errores de parsing, ausencia de texto, OCR fallido y localizador incorrecto. Revisores humanos deben adjudicar casos dudosos.
5. Informar resultados por formato/tipo y composición exacta del corpus. No interpretar similitud textual, tiempo o éxito del proceso como precisión semántica. No incluir documentos protegidos en Git ni en reportes públicos sin permiso.

Este protocolo está preparado, pero no se ha ejecutado como evaluación de calidad. El benchmark existente y los tests sintéticos no miden precisión OCR.

**Ejecución local observada (26/10/2026):** se ejecutó `scripts/benchmark_multiformat.py` sobre el corpus local disponible de 9 archivos, todos PDF: 971 páginas físicas y 0 fallos de archivo; 4 de los 9 PDF fueron señalados porque alguna página no tenía texto digital extraíble. El benchmark señaló posible necesidad de OCR; **no ejecutó OCR ni midió precisión**. Esta muestra no cubre DOCX/PPTX/XLSX ni se declara representativa; no sustenta cifras generales de rendimiento o calidad.

## 7. Casos mínimos cubiertos

- PDF digital sigue conservando número de página física y pipeline anterior.
- PDF sin texto pasa a `OCR_REQUIRED`; PDF mixto detecta que páginas físicas carecen de texto y habilita OCR selectivo (`--skip-text`). Original y copia OCR tienen hashes distintos.
- DOCX, PPTX y XLSX generan segmentos y localizadores distintos; tabla/celdas no se aplanan sin metadatos.
- Fórmula se conserva como expresión y no se calcula; caché se marca disponible/no disponible.
- Referencia a imagen no se presenta como texto OCR.
- El error de archivo inválido se refleja en job/extraction state; lectura de segmentos y búsqueda respetan scope del proyecto.
- La indexación reemplaza únicamente pasajes de la fuente y se mantiene idempotente; la búsqueda conserva el localizador del origen.

## 8. Fuera de alcance / trabajo futuro

- OCR de imágenes insertadas en DOCX/PPTX/XLSX, extracción de notas del presentador, figuras/gráficos con semántica y fórmulas recalculadas.
- Extracción de tablas científicas complejas y orden de lectura visual avanzado; se necesita benchmark representativo antes de seleccionar Docling u otro motor como extractor universal.
- Generación de respuesta narrativa fundamentada sobre el corpus, comprobación de citas, evaluación semántica de afirmaciones o escritura automática de tesis. B7 habilita segmentos recuperables para esos flujos; no los implementa.
- Descarga de recursos externos, scaping, OCR en nube, Scopus/WoS API, concesiones/licencias y acceso público al almacenamiento.

## 9. Verificación de cierre

**Puerta integral ejecutada el 26/10/2026:** `TESISMCP_DB_CONTAINER=tesismcp-local-pg ./scripts/verify_podman.sh` → `exit code 0`; **7/7** comprobaciones; duración total **381.76 s**. Resultados informados: auditoría grounded, chequeo Django, consistencia de migraciones, suite pytest completa (**362.49 s**), higiene de repositorio, consistencia doc-código y auditoría adversaria, todas aprobadas. El benchmark local descrito arriba es evidencia separada de esta puerta. Veredicto: `[APROBADO_CON_EVIDENCIA / EXIT_CODE_0]`. Este resultado no demuestra precisión OCR científica, rendimiento general, representatividad del corpus ni validez académica de los documentos recuperados.
