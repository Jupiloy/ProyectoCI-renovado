# Servidor MCP de TesisMCP

El servidor ofrece al cliente de IA herramientas para consultar el catálogo metodológico, crear proyectos, guardar una idea provisional, descubrir literatura relacionada y registrar una fuente de OpenAlex. Si hay un PDF permitido, su descarga y extracción se encolan. El transporte implementado actualmente es **stdio local**.

`buscar_semantic_scholar` permite una segunda búsqueda de catálogo. Sus resultados son exclusivamente metadatos. La demo local `test_local.py` ejecuta una simulación E2E completa validando el flujo transaccional y la ingestión del PDF real `INT1_ARIA_Multi_LLM_Framework_2025.pdf` con verificación estricta de citas literales en texto completo.

> 💡 **Para entender la arquitectura y el protocolo con analogías:** Consulta la [Guía de Arquitectura Explicada con Manzanitas](../docs/02_arquitectura_y_sistema/guia_arquitectura_con_manzanitas.md), donde se explica la analogía del restaurante y el mesero de comandas estandarizadas.

## Estado implementado

| Herramienta | Función |
| --- | --- |
| `estado_servidor` | Comprueba conexión, versión 0.2.0 y capacidades de los 7 capítulos. |
| `listar_pasos_mvp` | Lista los pasos metodológicos P01–P32 (Capítulos 1 al 7). |
| `consultar_detalle_paso` | Consulta entradas requeridas de cualquier paso (P01–P32). |
| `crear_proyecto` | Crea un proyecto cuyo titular es el usuario autenticado por token. |
| `obtener_estado` | Lee solo proyectos autorizados. |
| `registrar_idea` | Guarda la idea confirmada por el tesista con control de versión. |
| `explorar_idea` | Busca en OpenAlex; los resultados son únicamente metadatos. |
| `incorporar_fuente_openalex` | Consulta un ID OpenAlex y, si hay un PDF permitido, encola su descarga y extracción por página física. |
| `listar_fuentes` | Muestra la procedencia y el nivel de inspección de cada fuente. |
| `consultar_extractos` | Devuelve texto extraído, página física y hash; no evalúa si una afirmación es verdadera. |
| `procesar_ocr` | Encola OCR de un PDF escaneado del titular. |
| `listar_borradores` | Lista borradores DOCX cargados mediante la API. |
| `consultar_borrador` | Consulta Markdown por tramos de caracteres; no comprueba las fuentes citadas. |
| `consultar_citas_borrador` | Lista por tramos campos activos de cita Word/Zotero sin comprobar la fuente externa. |
| `analizar_fuente_grobid` | Encola la extracción TEI y bibliografía; devuelve `job_id`. |
| `consultar_analisis_grobid` | Consulta referencias extraídas automáticamente por tramos. |
| `indexar_fuente` | Encola embeddings multilingües de pasajes ligados a página física. |
| `consultar_trabajo` | Consulta estado, resultado o error de un trabajo autorizado. |
| `buscar_pasajes` | Recupera candidatos semánticos desde pgvector con fuente y página. |
| `guardar_paso` | Valida P01–P32 (Capítulos 1 al 7) y guarda una revisión confirmada por el tesista. |
| `consultar_capitulo` / `enviar_capitulo` | Consulta o envía una revisión de capítulo. |
| `asignar_asesor` | Asocia una cuenta existente al proyecto. |
| `consultar_observaciones` / `observar_fragmento` / `resolver_observacion` | Gestiona observaciones sobre texto exacto. |
| `decidir_capitulo` | Solicita cambios, aprueba o reabre con reglas de permiso y estado. |
| `cotejar_doi` | Encola el cotejo de metadatos Crossref. |
| `localizar_frase` | Devuelve coincidencias con página física y hash del texto extraído. |
| `vincular_evidencia` / `listar_vinculos_evidencia` / `revisar_vinculo_evidencia` | Crea candidatos y registra la decisión explícita del asesor. |

Las herramientas conectadas a Django llaman a `thesis.services` mediante `django_bridge.py`. El servicio de dominio concentra permisos y validaciones compartidas con la API web. MCP no acepta un `user_id` proporcionado por el modelo. La identidad proviene de `TESISMCP_MCP_TOKEN`, cuyo hash, vencimiento y revocación se comprueban en PostgreSQL.

## 🧠 Prompts MCP con roles secuenciales

El servidor expone 35 prompts MCP (`@app.prompt`). El mismo cliente LLM ejecuta los tres roles descritos abajo; no hay tres agentes autónomos. El backend no llama a una API de LLM, pero el cliente elegido por el usuario puede tener costos. Un prompt con `project_id` exige un token MCP válido y pertenencia activa al proyecto.

### 1. Secuencia de tres roles en el cliente LLM
Cada prompt de paso metodológico estructura automáticamente la interacción del LLM en tres fases consecutivas:
1. **Fase 1 (Asesor Metodológico):** Propone el contenido académico aplicando la Taxonomía de Bloom en infinitivo, títulos <= 20 palabras, signos `¿?` y delimitación formal.
2. **Fase 2 (Investigador Grounded):** Busca candidatos con `buscar_antecedentes_peru`; para anclar citas debe incorporar el PDF y usar `consultar_extractos` o `localizar_frase`. La revisión crítica sigue siendo necesaria.
3. **Fase 3 (Revisor de Contratos):** Valida que el objeto JSON cumpla con el contrato Pydantic del paso (`extra="forbid"`) y genera la llamada a `guardar_paso` con el `expected_version` actual de PostgreSQL.

### 2. Catálogo de Prompts Disponibles

| Tipo | Identificador | Descripción |
| --- | --- | --- |
| **Capítulo 1 (Tema y Alcance)** | `paso_p01_mapa_temas` a `paso_p05_redaccion_introduccion` | Generación de temas, matriz de factibilidad, ODS, delimitación del título y redacción de la introducción. |
| **Capítulo 2 (Problema y Justificación)** | `paso_p06_arbol_problema` a `paso_p08_originalidad_aporte` | Árbol de causas/efectos, preguntas con `¿?`, justificación en 4 dimensiones y originalidad/brecha. |
| **Capítulo 3 (Objetivos, Hipótesis y Variables)** | `paso_p09_objetivos_smart` a `paso_p12_operacionalizacion` | Objetivos con verbos de Bloom, preguntas alineadas, hipótesis general/específicas y matriz de operacionalización. |
| **Capítulo 4 (Revisión de Literatura)** | `paso_p13_ecuaciones_busqueda` a `paso_p20_referencias_apa7` (identificador histórico) | Ecuaciones de búsqueda, criterios, embudo PRISMA, matriz con citas grounded a PDFs y referencias; P20 propone IEEE para el piloto y conserva APA 7 en trabajos previos. |
| **Capítulo 5 (Marco Teórico y Conceptual)** | `paso_p21_seleccion_teorias` a `paso_p24_proposiciones_derivadas` | Teorías base, constructos con autor/año, modelo conceptual en Mermaid y proposiciones teóricas. |
| **Capítulo 6 (Metodología)** | `paso_p25_enfoque_diseno` a `paso_p29_redaccion_metodologia` | Enfoque cuantitativo, diseño preexperimental, procedimientos, validez (V de Aiken), ética y redacción. |
| **Capítulo 7 (Instrumentos de Recolección)** | `paso_p30_cuestionario_likert` a `paso_p32_piloto_calibracion` | Cuestionario Likert trazable a indicadores, guía de entrevista semiestructurada y calibración piloto. |
| **Rol Dedicado** | `rol_asesor_metodologico` | Sesión socrática enfocada en coherencia teórica, epistemológica y lineamientos UTP. |
| **Rol Dedicado** | `rol_investigador_grounded` | Búsqueda y auditoría documental con niveles de evidencia explícitos y revisión humana requerida. |
| **Rol Dedicado** | `rol_revisor_contratos` | Auditoría previa de payloads JSON contra los esquemas Pydantic antes de persistir en PostgreSQL. |

### 3. Hidratación Automática desde PostgreSQL
Al invocar cualquier prompt con el argumento opcional `project_id`, el servidor consulta PostgreSQL e inyecta directamente en el contexto:
* Título oficial registrado y código ODS.
* Versión actual de concurrencia optimista (`lock_version`).
* Preguntas, objetivos e hipótesis ya confirmados en la Matriz de Consistencia.
* Variables, dimensiones e indicadores ya operacionalizados.
* Lista de pasos completados en `StepProgress`.

## Configuración

Seguir primero la [guía del backend](../backend/README.md) para instalar dependencias, arrancar PostgreSQL, aplicar migraciones, crear un usuario y emitir un token MCP. Configurar para el proceso MCP `DJANGO_DEBUG=1`, `DATABASE_URL` y `TESISMCP_MCP_TOKEN`. Después iniciar:

```bash
.venv/bin/python -m mcp_server.server
```

Para descargar y extraer PDFs de OpenAlex, extraer PDFs cargados por la API, ejecutar `procesar_ocr`, `analizar_fuente_grobid`, `indexar_fuente`, `cotejar_doi` y convertir DOCX debe estar activo también `.venv/bin/python backend/manage.py run_document_worker` como proceso independiente. Las herramientas responden al encolar; `consultar_trabajo` permite saber cuándo concluye la operación. GROBID solo necesita estar activo para ejecutar su trabajo, no para encolarlo.

El cliente MCP debe lanzar ese comando desde la raíz del proyecto y pasar las variables de entorno. El token se muestra una sola vez al crearlo; no debe colocarse en documentos ni en el código. `test_local.py` ejecuta la demostración P01–P32, la revisión de siete capítulos y el rechazo de una fuente inventada. Usa un PDF real de ARIA, mientras que el caso metodológico y el coeficiente piloto son simulados.

## Alcance de la búsqueda

`explorar_idea` entrega títulos, autorías declaradas por OpenAlex, identificadores y enlaces candidatos. Marca `verification_level=METADATA_ONLY` y `full_text_inspected=false` incluso si hay un enlace PDF. `incorporar_fuente_openalex` consulta de nuevo el ID y, cuando hay un PDF público permitido, devuelve un trabajo en cola para descargarlo y extraer texto por página física. El tesista también puede cargar su PDF en la API web; esa carga encola la extracción. Después del trabajo, MCP puede consultar la fuente y sus extractos mediante `listar_fuentes` y `consultar_extractos`. `TEXT_CHECKED` solo acredita extracción de texto: la portada, los datos bibliográficos y las afirmaciones siguen sin verificación humana o semántica. Un PDF sin texto seleccionable queda en `OCR_REQUIRED`.

El titular puede llamar a `procesar_ocr` sobre una fuente `OCR_REQUIRED` si OCRmyPDF y los idiomas de Tesseract están instalados. El OCR no garantiza fidelidad de la transcripción; los extractos siguen requiriendo cotejo con el PDF original.

Los DOCX se cargan por la API web y se consultan por MCP. Sus campos de cita son metadatos presentes en el archivo del tesista: no prueban que la referencia exista ni que la página citada sostenga la frase.

Para conexiones MCP remotas se diseñará después autenticación y transporte Streamable HTTP; este servidor aún no los publica. [Especificación de transportes MCP](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports).
