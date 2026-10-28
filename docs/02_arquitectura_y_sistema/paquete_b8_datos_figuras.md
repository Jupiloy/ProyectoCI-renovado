# B8 — Datos, tablas, figuras y exportación reproducible

**Estado del bloque:** B8.1–B8.4 implementados y con puerta integral aprobada. En este corte: 7/7, total 479.66 s, pytest 457.26 s, exit code 0 (26/10/2026).  
**Corte B8.1:** migración `0041`; 54 modelos y 41 migraciones. Puerta integral 7/7, 383.36 s, pytest 364.62 s, exit code 0 (26/10/2026).  
**Objetivo:** conservar datos originales versionados, hacer que las operaciones tabulares y visuales se puedan repetir desde entradas identificadas y fijar sus resultados en el documento aprobado.

## Alcance y reglas

B8 no convierte una instrucción de IA en un resultado empírico. La fuente de cada cálculo es un dataset original identificado por hash y una receta declarativa versionada. El resultado calculado, la receta y la versión de datos deben poder inspeccionarse; las afirmaciones e interpretaciones académicas requieren revisión y evidencia propias.

- No ejecutar Python, SQL, macros, fórmulas ni código recibido dentro de un archivo del usuario.
- No modificar ni sobrescribir un dataset original. Una actualización crea otra versión inmutable.
- No recalcular fórmulas XLSX. El contenido de fórmulas y sus cachés puede ser incompleto o estar desactualizado; registrar ese límite.
- No inferir una muestra, variable, unidad, escala o diseño de estudio que el dataset no declare.
- No inventar resultados cuando falten datos o el tipo de análisis no se admita.
- El análisis estadístico avanzado, la codificación cualitativa, la integración de métodos mixtos y el tratamiento ético de datos de campo requieren contratos separados y no se anuncian como resueltos por B8.1.
- Las figuras/tablas generadas deben conservar fuente, filtro, transformaciones, versión del renderer y hash; su inserción en el manuscrito solo ocurre mediante acción explícita del tesista.

## Descomposición del bloque

| Incremento | Resultado verificable | Estado |
|---|---|---|
| B8.1 — Ingesta/versiones | Carga CSV UTF-8 y XLSX, hash/original conservado, metadatos estructurales, historial inmutable, idempotencia y descarga autorizada. | Implementado y verificado; pruebas focales 8/8; puerta integral 7/7, exit code 0. |
| B8.2 — Recetas/tablas | Operaciones declarativas permitidas, versionadas, validadas contra columnas, resultados tabulares reconstruibles con entradas y hash. Sin ejecución de código libre. | Implementado y verificado; 13 pruebas focales; puerta integral 7/7, exit code 0. |
| B8.3 — Figuras | Especificación de figura con tipos y columnas explícitos, PNG reproducible, preview, hash y metadatos de accesibilidad. | Implementado y verificado; puerta integral 7/7. |
| B8.4 — Documento/snapshot/exportación | Bloques tipados de tabla/figura ligados a versiones exactas; el snapshot congela IDs/hashes y el DOCX aprobado lee esas versiones sin recalcular. | Implementado y verificado; puerta integral 7/7. |

## B8.1 — Contrato implementado

### Formatos y límites

- `.csv` codificado UTF-8/UTF-8 BOM, encabezado en la primera fila y separador coma.
- `.xlsx` OOXML válido. Si tiene más de una hoja visible, el cliente debe enviar `sheet_name`; solo se procesa una hoja seleccionada por versión.
- Máximo de archivo: 30 MiB; máximo de 100 000 filas de datos y 256 columnas; paquete XLSX expandido máximo 250 MiB y máximo 10 000 miembros.
- Encabezados obligatorios, únicos sin distinguir mayúsculas, sin controles y de hasta 200 caracteres.
- Se ignoran filas completamente vacías. Filas con más celdas que encabezados se rechazan. Los tipos observados se resumen como `INTEGER`, `NUMBER`, `BOOLEAN`, `DATE`, `DATETIME`, `TEXT`, `MIXED` o `UNKNOWN`; esta clasificación es preliminar, no declara tipos científicos.
- XLSX se lee con valores almacenados. Fórmulas se cuentan y se advierte que sus cachés pueden estar desactualizados; no se evalúan. Valores caché ausentes quedan registrados.

### Persistencia, versión y permisos

- `ResearchDataset` es el contenedor con nombre/descripcion por proyecto.
- `ResearchDatasetVersion` conserva SHA-256, nombre original de base, formato, tamaño, conteo de filas/columnas, esquema observado, hoja seleccionada/metadatos, actor y fecha.
- Archivos se guardan bajo `MEDIA_ROOT/datasets/{project_id}/{dataset_id}/`; se rechazan rutas del cliente y formatos que no sean CSV/XLSX. La descarga recalcula y coteja el SHA-256 antes de responder.
- La creación y las nuevas versiones requieren titular activo del proyecto (`owner_only=True`). Participantes autorizados pueden listar, inspeccionar y descargar versiones del mismo proyecto. Un usuario ajeno recibe `NOT_FOUND`.
- Las versiones son append-only en PostgreSQL. Reintentos con igual clave y hash son idempotentes; misma clave y contenido distinto es conflicto. Una versión nueva requiere `expected_version` vigente.
- No se copia una segunda representación completa de las celdas a JSON/base de datos. B8.1 conserva archivo original y resumen de esquema; las recetas futuras leerán la versión original por hash.

### API

Rutas bajo `/api/v1/projects/{project_id}`:

| Método y ruta | Contrato |
|---|---|
| `POST /datasets` | multipart: `name`, `file`, `idempotency_key` UUID, `description` opcional, `sheet_name` opcional. Crea dataset y versión 1. |
| `GET /datasets` | Lista datasets del proyecto con su versión más reciente. |
| `POST /datasets/{dataset_id}/versions` | multipart: `file`, `expected_version`, `idempotency_key`, `sheet_name` opcional. Crea nueva versión inmutable. |
| `GET /datasets/{dataset_id}/versions` | Lista historial de versiones y hashes. |
| `GET /datasets/{dataset_id}/versions/{version_no}` | Devuelve metadatos de una versión. |
| `GET /datasets/{dataset_id}/versions/{version_no}/download` | Descarga el archivo original tras verificar hash. |

Los cuerpos de error siguen el `DomainError` del backend: formato/archivo inválido, tamaño excedido, permiso/not found, o conflicto de versión/idempotencia. Estos endpoints no calculan estadísticas ni producen figuras.

## B8.2 — Recetas declarativas y tablas (implementación actual)

### Propósito y límites

B8.2 convierte una versión exacta de CSV/XLSX en una tabla derivada con una receta JSON pequeña, permitida y determinista. La receta no ejecuta Python, SQL, macros, expresiones libres ni fórmulas del archivo. No genera texto académico, afirmaciones, análisis inferencial, tablas estadísticas avanzadas ni figuras. La interpretación científica, unidades, tratamiento de faltantes y aprobación de resultados siguen bajo responsabilidad del usuario/asesor; B8.2 no infiere ninguno de esos elementos.

Operaciones admitidas, en este orden:

1. `filters` opcional: hasta 64 condiciones AND. Operadores `EQ`, `NE`, `GT`, `GTE`, `LT`, `LTE`, `CONTAINS`, `IS_EMPTY`, `NOT_EMPTY`. Las comparaciones relacionales se admiten solo para columnas cuyo tipo observado es `INTEGER`, `NUMBER`, `DATE` o `DATETIME`; los vacíos no satisfacen comparaciones relacionales. `CONTAINS` compara texto sin distinguir mayúsculas. `IS_EMPTY` / `NOT_EMPTY` consideran vacío `null`, cadena vacía o texto compuesto solo de espacios.
2. `sort` opcional: hasta una orden por columna, `ASC` o `DESC`; vacíos siempre al final y el orden conserva estabilidad en empates.
3. `columns` obligatorio: proyección no vacía de nombres exactos y únicos del esquema importado. Filtros y orden pueden utilizar columnas que no se proyectan.
4. `limit` obligatorio: de 1 a 10 000. La respuesta indica `matched_row_count` y `truncated`; el límite no oculta si se excluyeron filas que coincidían.

Ejemplo de `spec`:

```json
{
  "columns": ["grupo", "valor"],
  "filters": [{"column": "valor", "operator": "GTE", "value": 4}],
  "sort": [{"column": "valor", "direction": "DESC"}],
  "limit": 1000
}
```

Las propiedades desconocidas hacen fallar la validación. La tabla serializada no puede superar 4 MiB. Un resultado de cero filas devuelve `EMPTY_RESULT` y no crea una versión de receta. Valores CSV conservan su forma textual; XLSX devuelve valores cacheados/serializados. Las fórmulas no se recalculan. Si el XLSX carece de caché de una fórmula, el valor queda vacío y la limitación queda vigente desde B8.1.

### Identidad, versiones, hashes e idempotencia

- `ResearchTableRecipe` identifica el nombre de una receta para una versión específica de dataset; no comparte una receta entre entradas diferentes.
- `ResearchTableRecipeVersion` guarda el número correlativo, clave idempotente, hash del archivo de entrada, JSON canónico de la especificación y SHA-256, tabla JSON resultante y SHA-256, versión del motor (`b8.2.1`), dimensiones, actor y fecha.
- Una edición crea una nueva versión inmutable y exige `expected_version` vigente. El primer guardado crea versión 1 sin `expected_version`. Un reintento con la misma clave y receta devuelve la versión existente; reusar la clave con receta distinta o enviar una versión obsoleta produce conflicto.
- Antes de calcular, el servicio comprueba el SHA-256 del original almacenado. La respuesta/lectura recalcula hashes de receta y resultado antes de devolverlos. PostgreSQL rechaza UPDATE/DELETE de versiones con `research_table_recipe_version_append_only`.
- La receta se vuelve a ejecutar sin escribir celdas derivadas sobre el original. Cada respuesta persiste un resultado congelado; la reconstrucción posterior se hace desde el original y el JSON versionado, su hash y la versión declarada del motor.
- Solo el titular crea/versiona recetas. Los participantes activos del proyecto pueden consultar recetas/versiones; el alcance de lectura se comprueba por proyecto.

### API implementada

Bajo `/api/v1/projects/{project_id}`:

| Método y ruta | Uso |
|---|---|
| `POST /datasets/{dataset_id}/versions/{version_no}/table-recipes` | Crea receta o versión. JSON: `name`, `spec`, `idempotency_key`; `expected_version` se requiere al editar una receta existente. |
| `GET /datasets/{dataset_id}/versions/{version_no}/table-recipes` | Lista recetas ligadas a esa versión exacta de dataset. |
| `GET /datasets/{dataset_id}/table-recipes/{recipe_id}/versions` | Lista historial inmutable de la receta. |
| `GET /datasets/{dataset_id}/table-recipes/{recipe_id}/versions/{version_no}` | Obtiene receta, resultado y hashes; falla si no concuerdan. |

Errores específicos: `VALIDATION_ERROR` (400), `VERSION_CONFLICT` (409), `OUTPUT_INVALID` (422), `EMPTY_RESULT` (422), `OUTPUT_TOO_LARGE` (413). `INVALID_DATASET` responde 400 y `DATASET_TOO_LARGE` 413. La API requiere sesión autenticada.

### Archivos B8.2

- Modelos: `backend/thesis/models/research_data.py`; exportaciones desde `backend/thesis/models/__init__.py`.
- Motor: `backend/thesis/services/research_tables.py`.
- Rutas/contrato: `backend/thesis/api/projects.py`.
- Manejo HTTP de errores de tamaño/dataset: `backend/config/api.py`.
- Migración `0042_researchtablerecipe_researchtablerecipeversion_and_more.py`; trigger append-only para versiones.
- Pruebas: `backend/thesis/tests/test_research_datasets.py`.

### Evidencia de cierre de B8.2

- Pruebas focales combinadas B8.1/B8.2: **13 pasaron**; 1 warning de deprecación emitido por `google.genai`; duración 68.36 s. Se cubren ingreso/versiones originales, filtros y orden numérico, proyección, límite/truncamiento, CSV, XLSX con caché de fórmula ausente, permisos, errores de esquema, idempotencia, versión obsoleta, API e inmutabilidad PostgreSQL.
- Puerta integral ejecutada con `TESISMCP_DB_CONTAINER=tesismcp-local-pg ./scripts/verify_podman.sh` el 26/10/2026: **7/7**, duración total **432.35 s**, pytest completa **410.33 s**, `exit code 0`; veredicto `[APROBADO_CON_EVIDENCIA / EXIT_CODE_0]`.
- Pasaron auditoría grounded (9/9 PDFs), Django `check`, `makemigrations --check --dry-run`, suite completa, higiene, consistencia doc-código (56 modelos, 42 migraciones, P01–P32/32, MCP 34 herramientas/35 prompts y enlaces) y auditoría adversaria.
- Una ejecución integral anterior detectó que los campos opcionales de `SelectDiscoveryCandidateIn` se habían quedado por error en `TableRecipeIn`; se corrigió el esquema y la prueba HTTP específica pasó (1/1). La puerta integral final se ejecutó después de ese arreglo y pasó 7/7.

Este cierre valida el incremento tabular B8.2 bajo datos de prueba; no demuestra validez científica ni comportamiento de usuario con datos reales. No incluye agregación estadística, inferencia, figuras, render del frontend, inserción al documento, snapshot ni exportación congelada.

## B8.3 — Figuras versionadas

### Alcance real

- `ResearchFigure` da nombre/identidad a una figura derivada de una `ResearchTableRecipeVersion` exacta. `ResearchFigureVersion` conserva cada PNG, número de versión, idempotencia, hash del resultado tabular de entrada, spec/hash, bytes/hash/tipo/dimensiones, versión concreta de Pillow/renderer, metadatos accesibles, actor y fecha. PostgreSQL impide modificar o borrar una versión.
- Tipos: `BAR`, `LINE` y `SCATTER`. Las figuras solo usan columnas ya seleccionadas por una tabla versionada; no vuelven a consultar el dataset ni ejecutan código, expresiones libres, SQL, Python o fórmulas.
- `BAR` requiere x categórica no vacía e y numérica finita; máximo 30 filas. `LINE` y `SCATTER` requieren x e y numéricas, ordenan por x y admiten hasta 500 filas. No se descartan datos inválidos silenciosamente. Este renderer todavía no admite fechas, barras de error, intervalos, múltiples series, pruebas inferenciales ni otro tipo de estadística.
- Dimensión fija 1200×800, PNG y fuente DejaVu Sans. `renderer_version` registra Pillow y el renderer. Se almacena la salida como archivo bajo `MEDIA_ROOT/figures/`; lectura/preview vuelve a comprobar bytes y SHA-256. Los títulos, etiquetas de ejes y texto alternativo son obligatorios; el sistema conserva los metadatos pero marca `accessibility_reviewed=false`, porque no certifica calidad del texto alternativo.
- Si la tabla de entrada fue truncada, se exige `accept_truncated_input=true`; la salida guarda que ese consentimiento se dio a nivel de operación y que la fuente estaba truncada. No convierte esa aceptación en aprobación académica.
- La creación/versionado está restringida al titular del proyecto; integrantes activos autorizados pueden consultar metadatos, historial y preview. Los recursos fuera del proyecto responden `NOT_FOUND`.
- `expected_version`, UUID de idempotencia e historial append-only protegen reintentos y versiones concurrentes. Una reescritura de spec crea otra versión; no sobrescribe PNG previos.

### API B8.3

Rutas bajo `/api/v1/projects/{project_id}`:

| Método/ruta | Función |
|---|---|
| `POST /datasets/{dataset_id}/table-recipes/{recipe_id}/versions/{table_version_no}/figures` | Genera una figura desde esa versión exacta. JSON: `name`, `spec`, `idempotency_key`, `expected_version` opcional al crear/obligatorio al editar y `accept_truncated_input` booleano. |
| `GET` en la colección anterior | Lista figuras de esa versión tabular. |
| `GET /datasets/{dataset_id}/figures/{figure_id}/versions` | Historial inmutable. |
| `GET /datasets/{dataset_id}/figures/{figure_id}/versions/{version_no}` | Metadatos, spec, hashes y accesibilidad. |
| `GET /datasets/{dataset_id}/figures/{figure_id}/versions/{version_no}/preview.png` | PNG servido después de verificar su hash. |

Propiedades exactas de `spec`: `chart_type`, `x_column`, `y_column`, `title`, `x_label`, `y_label`, `alt_text`; claves adicionales hacen fallar la validación. Errores: `VALIDATION_ERROR`, `TRUNCATED_INPUT_CONFIRMATION_REQUIRED`, `FIGURE_TOO_MANY_POINTS`, `OUTPUT_INVALID`, conflicto de versión/idempotencia o `NOT_FOUND`.

### Archivos B8.3

- Modelos e índices/constraints: `backend/thesis/models/research_data.py`; exports públicos en `backend/thesis/models/__init__.py`.
- Renderer y API de dominio: `backend/thesis/services/research_figures.py`; endpoints en `backend/thesis/api/projects.py`.
- `0043_researchfigure_versions.py`: dos modelos nuevos y trigger `research_figure_version_append_only`.
- Dependencias: Pillow y fuentes `fonts-dejavu-core` en la imagen. El renderer falla cerrado si Pillow o la fuente fijada no están disponibles.

## B8.4 — Documento, snapshot y exportación

- El árbol canónico admite schema v1 histórico y schema v2. Schema v1 mantiene los seis tipos de bloque existentes. Schema v2 permite además `{type:"data_table", id, table_version_id, result_sha256, caption}` y `{type:"figure", id, figure_version_id, output_sha256, caption}`. UUID de bloque y artefacto deben ser canónicos; hash hexadecimal minúsculo de 64 caracteres; caption obligatorio y limitado.
- Al guardar una revisión, el backend exige que las versiones indicadas pertenezcan al mismo proyecto y que los hashes de tabla o PNG coincidan. El Markdown de compatibilidad muestra placeholders legibles; el árbol JSON sigue siendo la representación que conserva los nodos de tabla/figura.
- Al enviar, `submit_chapter` valida otra vez cada referencia y congela en `ChapterSnapshot.document_artifacts_manifest` ID de bloque, ID exacto de versión, hash, caption y metadatos aplicables. El manifest forma parte de `payload_sha256`. Para un documento schema v2 el snapshot usa `format_version=3`; documentos textuales previos conservan sus versiones 1/2. La migración `0044` añade el manifest sin reescribir snapshots históricos; `0044` permite versiones de árbol 1 y 2.
- La exportación DOCX de un snapshot aprobado comprueba que el manifest cubra los bloques del árbol y valida cada versión/hash/archivo congelado. Renderiza tablas con valores del `result_json` inmutable y embebe la figura PNG exacta, incluido texto alternativo en la descripción del objeto. Si falta el artefacto o difiere su hash, falla cerrada.
- `GET /export/draft.docx` no cambia: sigue exportando las revisiones de pasos existentes. La exportación congelada aprobada es un endpoint/servicio separado. No se implementa PDF en B8.4.
- Crear una nueva versión de una tabla o figura después del envío no altera el snapshot: el manifest conserva la versión anterior. El flujo no calcula estadística nueva al exportar.
- El acceso al documento sigue siendo del titular para escritura. Los capítulos aprobados se exportan según controles de acceso existentes. Las figuras no constituyen resultados validados ni una interpretación académica.

### Archivos B8.4

- Árbol/normalización: `backend/thesis/services/chapter_documents.py`.
- Validación y materialización de manifest: `backend/thesis/services/document_artifacts.py`.
- Congelamiento: `backend/thesis/services/steps.py`; campos/modelos en `backend/thesis/models/chapters.py`.
- Render aprobado: `backend/thesis/services/exports.py`.
- Migración `0044_chapter_artifact_manifest.py` agrega `ChapterSnapshot.document_artifacts_manifest` y amplía el constraint de esquema de revisión a 1/2.
- Pruebas de tablas/figuras: `backend/thesis/tests/test_research_datasets.py`; documento, snapshot y DOCX aprobado: `backend/thesis/tests/test_chapter_snapshots.py`.

### Archivos implementados

- Modelos: `backend/thesis/models/research_data.py`; exports en `backend/thesis/models/__init__.py`.
- Servicio/parser: `backend/thesis/services/research_data.py`.
- Rutas: `backend/thesis/api/projects.py`.
- Migración: `backend/thesis/migrations/0041_researchdataset_researchdatasetversion_and_more.py`; trigger append-only `research_dataset_version_append_only`.
- Pruebas: `backend/thesis/tests/test_research_datasets.py`.

### Evidencia de cierre de B8.1

`TESISMCP_DB_CONTAINER=tesismcp-local-pg ./scripts/verify_podman.sh` ejecutado el 26/10/2026 → **7/7**; duración **383.36 s**; pytest completa **364.62 s**; `exit code 0`; veredicto `[APROBADO_CON_EVIDENCIA / EXIT_CODE_0]`. Pasaron auditoría grounded, `manage.py check`, consistencia de migraciones, pytest completa, higiene del repositorio, consistencia doc-código y auditoría adversaria. El resultado valida el incremento B8.1 y sus límites declarados; no cierra B8.2–B8.4.

## Evidencia de cierre B8.3–B8.4

- `python scripts/verify_project.py`, ejecutado dentro de la imagen de verificación conectada al PostgreSQL local el 26/10/2026: **7/7**, **479.66 s** en total; pytest completa **457.26 s**; **exit code 0**; `[APROBADO_CON_EVIDENCIA / EXIT_CODE_0]`.
- Pasaron auditoría grounded (9/9), `manage.py check`, `makemigrations --check --dry-run`, suite completa, higiene, sincronización de cifras/enlaces (58 modelos, 44 migraciones, P01–P32/32, MCP 34 herramientas/35 prompts) y auditoría adversaria.
- La prueba focal añadida para render DOCX de tabla/figura con snapshot congelado pasó junto con el resto de la suite; 2 casos que fallaron en la primera ejecución por lectura de `FileResponse` y acceso al objeto Picture se corrigieron y repitieron: **2/2, 7.04 s** antes de la puerta final.
- El resultado demuestra el mecanismo con pruebas automatizadas y datos de prueba; no valida datos de investigación, la interpretación científica, estilo institucional completo, presentación PDF ni uso del frontend.

## Criterio de alcance cerrado

B8.1–B8.4 quedan implementados y pasan la puerta integral descrita. El prototipo genera DOCX con tablas y figuras congeladas; no entrega exportación PDF ni valida científicamente las interpretaciones. La operación posterior de guardar un capítulo/documento sigue la revisión humana normal; los artefactos en el DOCX no se convierten en afirmaciones académicas automáticas.
