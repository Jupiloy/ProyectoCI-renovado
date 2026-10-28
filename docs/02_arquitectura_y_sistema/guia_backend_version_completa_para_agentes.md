# Guía de desarrollo del backend para la versión completa de TesisMCP

**Estado:** especificación de destino y traspaso para agentes de código. **Actualizado:** 26/10/2026. Esta guía distingue el código observado de las capacidades propuestas. No acredita que el producto final ya exista.

## 1. Lectura obligatoria y regla de interpretación

1. Leer [AGENTS.md](../../AGENTS.md) para reglas de evidencia, seguridad y verificación.
2. Leer la [Guía Maestra para Agentes](../../GUIA_AGENTE.md), la [visión integral](../01_vision_y_alcance/propuesta_integral_tesismcp_y_decisiones_de_diseno.md), el [estado verificable del producto](../07_desarrollo_prototipo/estado_version_producto.md) y el [paquete de especificación integral](./especificacion_integral_backend.md).
3. Inspeccionar el código, las migraciones y los contratos relevantes antes de crear otros. La [referencia de rutas reales](../../backend/README.md) y el [modelo físico](./modelo_datos_fisico.md) sirven como mapa, pero el código vigente determina qué está implementado.
4. Tratar las menciones al MVP de semana 12/P01–P08 en documentos históricos como una estrategia de entrega pasada. **P01–P32 y capítulos 1–7 son la base actual**, no el límite final: el producto objetivo incluye preparación, recolección autorizada, análisis de datos reales, resultados y entrega. El [orden metodológico revisado](../03_metodologia_y_prompts/propuesta_orden_metodologico_revisado.md) es una propuesta editable; el [contrato de recorrido y prompts configurables](./contrato_recorrido_y_prompts_configurables.md) define la primera entrega de backend priorizada.
5. Etiquetar en cada tarea: **IMPLEMENTADO**, **PARCIAL**, **PENDIENTE**, **DEPENDIENTE DE PERMISO EXTERNO** o **DECISIÓN ABIERTA**. Una propuesta de esta guía nunca se reporta como funcional sin evidencia del código y una ejecución real.

Para especificar todos los dominios, consultar también el [inventario de brechas](./inventario_brechas_backend.md), los [contratos de dominio](./contratos_dominio_backend.md), los [contratos de API](./contratos_api_backend.md), la [matriz de cuentas y permisos](./matriz_permisos_y_cuentas_backend.md), los requisitos de [seguridad/datos/operación](./seguridad_datos_operacion_backend.md), el [registro de decisiones](./registro_decisiones_backend.md), el [plan de entregas/Definition of Done](./plan_entregas_backend.md), la [especificación de búsqueda y evidencia](./especificacion_busqueda_y_revision_de_evidencia.md) y la [especificación de generación IA y destino de resultados](./especificacion_generacion_ia_y_resultados.md). B5.1 ya tiene jobs, worker, rutas y adaptador Gemini; la llamada real sigue pendiente de credenciales del servidor. B1.1–B1.3 implementan snapshot, revisión/aprobación ancladas y exportación DOCX aprobada. B1+B2.2 añade documento canónico y B1+B2.3 conecta P05/P29 mediante preview de diff y aceptación versionada; consultar el [paquete B1+B2.3](./paquete_b1_b2_3_diffs_ia_documento.md). Lo siguiente es probar la ida/vuelta con frontend y anclar comentarios a bloques; no reconstruir snapshots, revisión, exportación ni aceptación existente.

## 2. Producto que debe sostener el backend

La web propia de TesisMCP será el espacio principal del tesista y del asesor. Contendrá exploración de temas, ruta metodológica, biblioteca de fuentes, editor enriquecido propio, citas, tablas/figuras, revisión y seguimiento. MCP es una conexión adicional sobre los mismos servicios de dominio. Zotero se integra como gestor bibliográfico; Word, LibreOffice, PDF y LaTeX son salidas o formas de continuar fuera de la plataforma. Collabora Online no forma parte de la propuesta.

El backend actual ayuda a estructurar y redactar borradores hasta el capítulo 7. El destino funcional acompaña la tesis completa: prepara instrumentos, registra datos reales, ayuda a analizarlos y redacta resultados/discusión/conclusiones con evidencia y revisión humana. No inventa resultados de campo ni convierte una propuesta de IA en una aprobación académica. Se construye por entregas; el recorrido y los prompts configurables se priorizan ahora para que el profesor pueda revisar y cambiar el método sin rehacer la infraestructura.

### Invariantes del producto

- El tesista confirma decisiones académicas; el asesor decide sobre revisiones identificables. Un mismo asesor puede cubrir funciones temáticas y metodológicas.
- Una fuente descubierta por metadatos no se presenta como PDF leído. Toda afirmación derivada de texto conserva archivo/versión, página física o localizador y pasaje.
- La búsqueda asistida en Scopus/WoS funciona sin API: generar ecuación editable, guardar base/filtros/fecha, abrir el sitio oficial y procesar la exportación del usuario. API es extensión opcional y no bloquea la búsqueda manual ni el análisis de archivos.
- La revisión de citas separa identidad bibliográfica de apoyo textual a una afirmación. Una evaluación automática debe mostrar pasaje/localizador y nivel de acceso; toda edición/reemplazo requiere diff y aceptación del tesista.
- La IA propone resultados tipados y trazables; los servicios del backend validan y persisten únicamente tras una acción autorizada.
- Web, MCP y trabajos en segundo plano aplican los mismos permisos, versiones, transiciones y reglas de evidencia.
- Los capítulos y exportaciones conservan la versión de metodología, citas, datos, figuras y texto con la que fueron producidos.
- Invitados ayudan con tareas delimitadas (p. ej., estrategia de búsqueda o revisión temática); reciben solo los materiales concedidos y no aprueban el capítulo en lugar del asesor.

## 3. Mapa comprobado del backend actual

| Dominio | Observado en código/documentación | Brecha frente al destino |
| :--- | :--- | :--- |
| Identidad y proyectos | `User`, `Project`, `ProjectParticipant`; Django Ninja con sesión, `McpAccessToken`; un `OWNER` y un `ADVISOR` activos por proyecto. | Definir asesoría temática/metodológica como funciones asignables; extender participantes solo si un caso real exige varios asesores. |
| Método | Catálogo `P01`–`P32`, contratos Pydantic, `StepProgress`, materializadores y guardado transaccional. B5 permite modo legado secuencial o grafo configurable y tareas `USR_...`. B5.1 implementó jobs, worker, validación local, `output_schema` custom, aceptación/rechazo y adaptador Gemini. B1+B2.2 incorporó documento JSON por capítulo; B1+B2.3 añade diff/aceptación para P05/P29. | El proveedor IA está deshabilitado por defecto y la llamada real requiere credenciales. El árbol y diff deben probarse con editor frontend; comentarios siguen por offsets Markdown; otras tareas no se mapean al documento. |
| Consistencia e instrumentos | Perfil, preguntas/objetivos/hipótesis, variables, dimensiones, indicadores, instrumentos e ítems relacionados. | Adaptar reglas al enfoque y a la guía aplicable; no forzar variables en investigaciones que no las usan. |
| Fuentes | OpenAlex, Semantic Scholar, ALICIA/peruanas y Crossref en adaptadores/servicios; PDF cargado, extracción, OCR, GROBID y pgvector. `SourceDocument` externo hoy exige `openalex_id`. | Importación RIS/BibTeX/CSV/XLSX y procedencia de múltiples proveedores; conectores con permiso cuando estén disponibles. |
| Evidencia | `SourceExcerpt`, `SourcePassage`, `EvidenceLink`; P16 exige PDF, página y citas literales. | Cobertura de citas del editor, discrepancias de metadatos, auditoría de afirmaciones y visualización de soporte. |
| Revisión | `ChapterRevision` inmutable, comentarios anclados por índices Unicode sobre `content_md`, estados de capítulo y eventos. `save_step` crea una revisión por guardado de paso; `submit_chapter` y `decide_chapter` toman la revisión más reciente. | Definir y congelar una instantánea **completa** del capítulo para revisión/aprobación; conectar el editor sin perder anclas ni historial. |
| Trabajos | `DocumentJob` procesa documentos; `WorkflowTaskExecution` guarda historial de outputs de tareas custom; `AIGenerationJob` gestiona estados, contexto fijado, salida y decisión humana; Gemini implementa la interfaz LLM. | El worker y el ciclo de jobs existen. La llamada real Gemini requiere credenciales y no se verificó. No reutilizar `DocumentJob` para generación sin demostrar que sus invariantes documentales soportan ese ciclo. |
| Citas y salidas | P20 admite `IEEE` y `APA_7`; DOCX actual concatena revisiones Markdown y conserva formato básico de borrador; lector DOCX detecta ciertos campos Word/Zotero. | IEEE para el piloto; citas dinámicas dentro de TesisMCP; exportaciones fieles y campos Zotero externos solo si se prueban. |
| Experiencia web | API `/api/v1/` y Django Admin/Unfold del asesor. | Frontend propio del tesista y contrato de contenido para su editor; todavía no existe como producto implementado. |

Puntos de código para empezar: [modelos](../../backend/thesis/models/__init__.py), [pasos](../../backend/thesis/services/steps.py), [contratos](../../backend/thesis/services/step_contracts.py), [revisión](../../backend/thesis/services/reviews.py), [fuentes](../../backend/thesis/services/sources.py), [trabajador](../../backend/thesis/services/document_jobs.py), [exportación](../../backend/thesis/services/exports.py) y [rutas API](../../backend/thesis/api/projects.py). La documentación anterior sobre el MVP contiene planes históricos, no una orden de reiniciar el backend.

### Discrepancias funcionales que el agente debe resolver antes del editor

1. **Unidad de revisión:** `save_step` crea `ChapterRevision(step_code, content_md)` en cada guardado. `submit_chapter` registra la revisión más reciente y `decide_chapter` la señala como aprobada; `export_draft_docx` ensambla, en cambio, la última revisión de **cada paso**. El código no garantiza que la revisión aprobada congele todo el contenido que luego aparece en el documento. Diseñar una instantánea completa de capítulo con los IDs/versiones de los pasos, citas y figuras que contiene; decidir si la nueva entidad debe ser distinta de las revisiones de paso existentes. No reinterpretar registros antiguos como instantáneas completas por el nombre de la tabla.
2. **Salida estructurada histórica:** `StepProgress.output_json` se reemplaza cuando un paso vuelve a guardarse, mientras `ChapterRevision` conserva texto, `step_code` y hash, pero no una copia de esa salida. La metodología configurable y la auditoría requieren versiones inmutables también de los resultados estructurados. Diseñar migración/lectura de datos legados antes de cambiar el contrato.
3. **Puerta de aprobación:** `save_step` comprueba que el paso previo esté `COMPLETED`, pero no comprueba que el capítulo anterior esté `APPROVED`. La regla de aprobación progresiva mencionada en documentos históricos no queda garantizada por ese servicio. Formalizar qué decisiones requieren aprobación previa y cuáles tareas independientes (p. ej. búsqueda de antecedentes) pueden adelantarse como borradores; los resultados dependientes deben fijarse a la versión aprobada del contexto.
4. **Anclas de comentarios:** los índices Unicode actuales se validan contra `content_md` de una revisión específica. Un editor enriquecido necesita anclas estables y un mecanismo verificable para convertir selección visual a la versión canónica. Los comentarios de revisiones anteriores siguen ligados a su versión original.

**Criterio para B1:** al aprobar un capítulo debe existir una instantánea inmutable que reconstruya exactamente el capítulo que vio el asesor; la exportación de esa revisión debe usar la misma instantánea. Ningún cambio posterior en `StepProgress`, Zotero o un paso vecino modifica retroactivamente lo aprobado. El agente debe demostrar además el comportamiento de la puerta entre capítulos y el permiso de adelantar trabajo bibliográfico independiente.

### Restricciones estáticas del catálogo que necesitan decisión metodológica

El [contrato actual](../../backend/thesis/services/step_contracts.py) codifica elecciones de un caso concreto. P01 exige de 5 a 10 temas y P02 compara exactamente 3; eso no representa por sí solo la vista de cinco temas destacados y el archivo de alternativas que pidió el usuario. P04 obliga a incluir de una a dos variables, unidad, lugar y año literalmente en el título, además del máximo de 20 palabras; esto puede no corresponder a estudios cualitativos ni a la secuencia de delimitación revisada con el profesor. P14, P16 y P21 tienen topes de año fijados en 2026; P16 admite hasta 20 estudios y P20 hasta 50 referencias. P20 admite IEEE y APA 7; el piloto prioriza IEEE sin perfil por proyecto implementado. P32 recibe un coeficiente declarado por el cliente y aplica un umbral fijo al estado `CALIBRADO`, sin derivarlo de respuestas piloto originales.

El agente debe clasificar cada límite como regla protegida, política institucional versionada, valor por defecto de una plantilla o restricción histórica a retirar. Cambiar números directamente en Pydantic sin resolver esa clasificación puede romper proyectos guardados y crear una norma académica falsa. Conservar lectura de versiones anteriores y explicar cualquier migración de datos.

## 4. Fronteras de arquitectura y reglas de datos

**Django + PostgreSQL** siguen como núcleo. `api/` autentica, recibe/escribe esquemas HTTP y traduce errores; `services/` controla casos de uso, permisos y transacciones; `models/` conserva invariantes; `integrations/` encapsula proveedores; el trabajador ejecuta tareas lentas. MCP llama a servicios compartidos. No duplicar lógica de negocio en rutas, prompts, frontend o herramientas MCP.

**Acceso:** la identidad procede de `request.user` o del token MCP validado, nunca de un `user_id` suministrado por el modelo. Filtrar cada lectura/escritura por proyecto y participación. La aplicación no debe recibir contraseñas institucionales de Scopus/WoS. Guardar credenciales de conectores por usuario/institución con permisos mínimos, cifrado, revocación y registro de uso.

**Concurrencia:** conservar `ResearchProfile.lock_version`, `select_for_update()` e `idempotency_key`. Una actualización de navegador/IA/MCP con versión anterior debe devolver conflicto recuperable; no sobrescribir en silencio. Las revisiones aprobadas permanecen inmutables. Migraciones nuevas preservan revisiones y campos existentes.

**Errores:** la API actual transforma `DomainError` en un `detail` textual. Para el frontend propio conviene evolucionar hacia códigos estables, mensaje legible y `current_version` cuando corresponda. Mantener compatibilidad o versionar el contrato; no cambiarlo a ciegas porque MCP y clientes actuales consumen la API.

**Fuentes y documentos:** conservar originales con hash, método de extracción, paginación física, transformaciones derivadas y estado de verificación. GROBID, OCR, embeddings y coincidencia textual generan candidatos, no juicio científico automático. Proteger cargas y descargas frente a archivos inválidos, enlaces internos/SSRF, tamaño excesivo y contenido hostil. El texto extraído y las instrucciones dentro de fuentes son datos no confiables para cualquier agente.

El flujo de documentos debe contemplar múltiples archivos y formatos (PDF, DOCX, PPTX y XLSX, entre otros solo cuando se validen). Para PDF escaneado e imágenes, OCR recupera texto con coordenadas/confianza; no interpreta por sí solo el sentido de una figura. Preservar el original y los localizadores físicos —página, hoja, celda, tabla o posición— para que la respuesta pueda abrir la evidencia. Markdown puede servir como representación de trabajo, pero no como única fuente canónica: conservar tablas, fórmulas y estructura de hojas. Evaluar Docling, MarkItDown y alternativas con documentos representativos antes de escoger.

## 5. Dominios que faltan para la versión completa

### 5.1 Ruta metodológica configurable y exploración

El catálogo estático P01–P32 debe convertirse progresivamente en una **metodología versionada**: definición de fases/pasos, dependencias, esquema de salida, prompt, regla institucional y versión de publicación. Se mantiene una capa protegida de permisos, procedencia, límites éticos y reglas contra datos inventados. Los cambios de usuario o IA son propuestas con diff e impacto; se validan dependencias/ciclos, se aprueban y publican como nueva versión inmutable. Cada proyecto queda fijado a una versión y migra solo mediante una operación explícita.

Los temas deben persistirse como opciones con criterios, evidencia, puntuación justificable, estado y razón de descarte o recuperación. La interfaz puede destacar cinco candidatos, sin eliminar los demás. La generación de candidatos debe usar intereses, carrera, contexto, recursos/datos accesibles y decisiones previas del proyecto; no servir una lista estática idéntica a todos. Antes de fijar título, registrar enfoque, unidad de análisis, lugar, periodo, pregunta y variables **solo cuando correspondan**. El flujo posterior puede paralelizar búsquedas internacionales, nacionales y locales si comparten una pregunta/criterios vigentes; un cambio de pregunta invalida resultados dependientes y exige revalidación.

**Migración requerida:** revisar cómo `step_code` y `output_json` actuales se vincularán a definiciones versionadas antes de introducir tablas nuevas. Mantener lectura de proyectos antiguos y no reescribir `ChapterRevision` histórico. Los nombres concretos de tablas y el formato de prompt se deciden con una migración de datos documentada.

### 5.2 Biblioteca científica, importación y procedencia

Dar prioridad a un importador de exportaciones realizadas por el usuario: RIS, BibTeX y CSV; XLSX cuando exista muestra real. Guardar archivo original, proveedor declarado, fecha, consulta/filtros si el usuario los proporciona, identificador del registro y un informe de filas rechazadas. Detectar duplicados por identificadores y similitud sin fusionar silenciosamente registros conflictivos; una misma obra puede conservar varias procedencias.

**Restricción real a resolver:** hoy `SourceDocument.Kind.EXTERNAL` exige `openalex_id` en la base. No insertar registros Scopus, WoS o Zotero con un identificador OpenAlex ficticio. Diseñar una migración que admita registros externos de otros orígenes y, si hace falta, una relación de procedencias por fuente. Mantener la unicidad de archivos/identificadores y la compatibilidad con las fuentes OpenAlex existentes.

La primera ruta de Scopus/WoS es manual asistida: elaborar la ecuación y filtros, abrir el proveedor y aceptar el archivo exportado por la persona. La búsqueda funcional no requiere API. Un API puede investigarse como extensión si agrega una capacidad necesaria y se comprueban entitlement/permiso/uso; no es una dependencia para B2 ni para leer documentos. La automatización de navegador no pertenece al flujo base. No asumir que la cuenta estudiantil autoriza una integración multiusuario; no guardar contraseñas ni evadir CAPTCHA, límites o controles. No atribuir a Scopus/WoS un resultado obtenido solo de OpenAlex. Los conectores opcionales exponen proveedor, método, cuota, fallo, fecha y campos recibidos.

Los antecedentes deben explicar qué concepto, método, variable/constructo, instrumento o hallazgo del estudio se toma como referencia y en qué pasaje se apoya. Clasificar internacional/nacional/local según criterios explícitos; no inferir pertinencia por país o palabras coincidentes. P16 ya exige evidencia literal: ampliar sin rebajar ese umbral.

### 5.3 Zotero y citas en el editor propio

**Estado B4:** existe conexión Zotero OAuth 1.0a de solo lectura a biblioteca personal, importación de metadatos a `SourceDocument` y cifrado de la API key. No hay selección de colecciones, sincronización de cambios ni escritura a Zotero; los metadatos importados permanecen `UNVERIFIED_METADATA`. La ida/vuelta OAuth real requiere registrar la app/configurar secretos y aún no se ha comprobado. No copiar la aplicación Zotero ni depender de que Zotero esté abierto para redactar en TesisMCP. Los endpoints y permisos físicos constan en [implementación B4](./implementacion_b4_citas_ieee_zotero.md).

En el editor web, cada cita debe apuntar a una referencia interna y, cuando la afirmación lo requiera, a un `EvidenceLink`/pasaje. Al cambiar el orden de citas, el backend/renderer recalcula la numeración y bibliografía IEEE desde referencias estructuradas. Un `[12]` escrito como texto no prueba procedencia. La vista de cita debe permitir abrir fuente, página y nivel de verificación.

**Estado B4:** el editor canónico puede generar marcas y bibliografía IEEE preliminar desde ocurrencias y metadatos congelados; el DOCX del snapshot aprobado renderiza ese manifest. No es todavía formato IEEE completo por tipo documental. P20 admite IEEE y conserva APA 7 por compatibilidad; sigue siendo una superficie separada de las citas estructuradas. El piloto prioriza IEEE por indicación del profesor, sin afirmar que toda tesis UTP deba usarlo. Un DOCX con referencias estáticas y uno cuyos campos Zotero se refrescan en Word/LibreOffice son garantías distintas; B4 solo ofrece lo primero y no afirma que esté completo según IEEE.

### 5.4 Documento canónico y revisión desde el editor web

El frontend tendrá un editor visual propio. El backend ya recibe contenido **estructurado y versionado** con encabezados y párrafos; B4 añade marcas de citas semánticas vinculadas a fuentes. Notas, tablas, figuras y referencias cruzadas aún deben diseñarse fuera del árbol v1. El editor frontend/ida-vuelta sigue pendiente. El formato concreto del árbol de documento se elige conjuntamente con el frontend tras una prueba de ida y vuelta; no atar el dominio a un editor JS específico ni guardar solo HTML libre como fuente de verdad.

`ChapterRevision.content_md` y los comentarios por offsets Unicode son el contrato actual. Definir una transición compatible: mantener las revisiones antiguas legibles, producir una proyección Markdown cuando la necesiten los servicios existentes y asociar nuevas anclas a una revisión y posición estable. Si cambia el texto, la observación anterior queda ligada a su revisión; no moverla por conjetura. Autosave y generación de IA crean borradores; la presentación al asesor produce una revisión inmutable. Explicar al usuario los conflictos entre pestañas o agentes.

La plataforma debe saber qué texto fue escrito por el tesista, sugerido por IA, modificado y aceptado, sin etiquetar falsamente autoría. Las exportaciones se generan desde una revisión concreta y congelan citas, tablas, figuras, reglas y datos de esa revisión.

### 5.5 IA y tareas multiagente dentro de la web

El backend actual tiene un camino opcional B5.1 que llama Gemini desde jobs del servidor y también herramientas MCP locales; ninguno implementa todavía el despacho web→agente BYOA→web. El objetivo principal no es que Django invoque necesariamente una API comercial de modelo: la web debe crear un job por la API de TesisMCP, un conector compatible debe entregarlo al runtime/agente vinculado por el usuario, y ese agente debe consultar herramientas por MCP. Diseñar gateway, estados/eventos, autenticación vinculada, permisos por proyecto, contexto versionado, cancelación y resultados tipados antes de codificar. El camino Gemini server-side se conserva como opción separada y explícita. Mantener separado el modelo del guardado canónico: propuesta → validación de esquema/evidencia → vista de cambios → aceptación del tesista → revisión del asesor cuando corresponda. Ver [arquitectura BYOA, API y MCP](./arquitectura_byoa_api_mcp.md).

Funciones candidatas: exploración de temas, viabilidad, diseño de búsqueda, recolección por fuente/región, deduplicación, extracción, síntesis, contraevidencia, coherencia metodológica, instrumentos, redacción, auditoría de citas, adaptación de estilo propio, figuras y respuesta a observaciones. Ejecutar ramas independientes en paralelo y unir resultados con su procedencia; las decisiones que alteran pregunta, método o población requieren una puerta de aprobación. Cada tarea registra tipo, versión de contexto, entradas/IDs de fuentes, prompt/modelo/versiones, resultado, advertencias, costo/tiempo y estado. No reutilizar silenciosamente una respuesta generada con contexto obsoleto.

El perfil de escritura personal se crea con muestras autorizadas por el estudiante, se puede corregir y borrar, y no prevalece sobre citas, rigor, normas o autoría. No usarlo para imitar a otra persona o ocultar la procedencia de las sugerencias.

Los agentes son capacidades de trabajo invocables, no nuevos roles institucionales obligatorios. Además de redactar, pueden idear/valorar temas, preparar búsquedas por fuente y ámbito, deduplicar, extraer y verificar evidencia, localizar contradicciones, mapear conceptos y métodos, revisar instrumentos, comprobar citas/coherencia, responder observaciones y preparar visualizaciones. El tesista y su asesor siguen siendo los actores principales; el mismo asesor puede ejercer funciones temáticas y metodológicas. Bibliotecarios, expertos, administradores institucionales u otros apoyos entran como invitaciones, herramientas o extensiones optativas. n8n puede orquestar integraciones externas si aporta valor, pero WhatsApp está fuera del alcance y ninguna automatización externa debe duplicar permisos o reglas del dominio.

**Revisión afirmación–cita:** el editor permite seleccionar una cita/afirmación o solicitar revisión de un capítulo. El backend guarda la versión revisada, los pasajes utilizados y la calidad de acceso. La salida preliminar distingue `SUPPORTS`, `PARTIAL_SUPPORT`, `CONTRADICTS`, `UNRELATED`, `INSUFFICIENT_ACCESS` y `NOT_ASSESSED`, separada de estados humanos de aceptación. El sistema puede localizar fuentes candidatas mediante descubrimiento abierto o resultados importados; solo propone respaldo si recupera un pasaje verificable. Muestra evidencia y diff antes de cambios; nunca reemplaza una fuente o reescribe el manuscrito por sí solo. Consultar la [especificación funcional](./especificacion_busqueda_y_revision_de_evidencia.md) para alcance y aceptación.

**Apoyos invitados:** no crear un rol global para cada experto o bibliotecario. Si se implementa la invitación, registrar quién invita, la tarea, los recursos compartidos, permisos, aceptación, vencimiento/revocación y respuesta. El bibliotecario reduce armado y revisión de búsquedas; el experto revisa una pregunta/instrumento/afirmación acotados; la configuración institucional de guías es una administración separada sin lectura por defecto de tesis. El tesista elige qué incorporar y el asesor conserva aprobación de capítulo. Preparar paquetes de revisión, ecuaciones, fuentes y diferencias para que nadie repita manualmente trabajo ya hecho.

### 5.6 Tablas, figuras y exportaciones

Registrar datos de entrada con procedencia, versión, unidades y permisos. Las transformaciones y cálculos de una tabla o figura deben ser deterministas y reproducibles; la IA puede proponer una visualización o explicación, pero las cifras renderizadas salen de los datos aprobados. Una edición de datos dispara validación, recálculo y nueva versión; el documento exportado conserva la instantánea usada.

El exportador actual es un borrador DOCX básico. La ruta completa debe producir documentos desde el mismo contenido canónico, con citas IEEE verificables, estructura de capítulos, tablas/figuras con fuente y metadatos de versión. DOCX/PDF son salidas prioritarias; LaTeX/BibTeX puede añadirse sobre el mismo modelo. No marcar un archivo como tesis lista para presentar sin comprobar la guía institucional, carátula, anexos y evidencia necesaria.

## 6. Contratos para implementar nuevas capacidades

### Conceptos de datos a diseñar, sin crear tablas por anticipado

| Concepto | Identidad y vínculos mínimos | Invariante que debe conservarse |
| :--- | :--- | :--- |
| Opción de tema | Proyecto, origen/tema padre, criterios, estado, versión. | Una opción no desaparece al dejar de estar entre las más viables; se conoce por qué cambió su valoración. |
| Versión metodológica | Definiciones de pasos, dependencias, prompts, reglas y publicación. | Un proyecto y sus revisiones conservan la versión usada; el grafo publicado no contiene ciclos. |
| Registro bibliográfico y procedencia | Obra/DOI/identificadores, una o varias fuentes de metadatos, archivo original de importación. | Un registro Scopus/WoS/Zotero conserva la procedencia real y las discrepancias entre proveedores. |
| Conexión Zotero | Usuario autorizante, biblioteca/colección, permisos, estado y cursor de sincronización. | Revocar conexión impide nuevas consultas; no destruye automáticamente citas ya aprobadas. |
| Borrador y revisión de capítulo | Proyecto, capítulo, versión de método, contenido estructurado, pasos/fuentes/citas/figuras usadas. | La revisión entregada al asesor se reconstruye exactamente aun si el borrador cambia después. |
| Ocurrencia de cita | Revisión, referencia, localizador y vínculo de evidencia cuando aplique. | La numeración IEEE se deriva de ocurrencias ordenadas; no se guarda como único dato un corchete de texto. |
| Evaluación afirmación–fuente | Ancla/afirmación, ocurrencia, documento/hash, pasajes/localizadores, extractor y estado de acceso. | Juicio automático y decisión humana son estados diferentes; cambios de entradas obsoletizan evaluaciones anteriores. |
| Invitación/paquete de apoyo | Proyecto, actor invitante/invitado, tarea, recursos, permisos, vencimiento, aceptación y revocación. | El acceso invitado queda limitado a materiales concedidos y su aporte no altera contenido ni aprobación canónicos. |
| Datos y figura | Datos originales, transformación, especificación visual, unidades y versiones. | Una figura exportada puede reproducirse desde la instantánea de datos/transformación aprobada. |
| Ejecución de IA | Proyecto, actor, versión de contexto, proveedor/modelo, tarea, entrada/salida, estado y aceptación. | Una salida obsoleta o no aceptada nunca modifica la versión canónica por sí sola. |

Esta tabla describe información necesaria, no nombres obligatorios de modelos. Antes de crear cada entidad, comparar con modelos existentes, elegir claves/índices y documentar migración, retención y permisos. Evitar un segundo almacén del mismo contenido que pueda divergir del documento aprobado.

### Operaciones lógicas esperadas de la API

| Operación | Resultado observable | Condición importante |
| :--- | :--- | :--- |
| Guardar borrador del editor | Nueva versión de borrador o respuesta de conflicto con versión vigente. | Solo actor autorizado; contenido validado y esquema compatible. |
| Enviar capítulo a revisión | ID de instantánea inmutable y estado `READY`. | Capítulo ensamblado y prerrequisitos académicos cumplidos. |
| Comentar, resolver, solicitar cambios y aprobar | Evento/revisión/estado nuevos. | El asesor ve exactamente la versión que aprueba; no hay comentarios abiertos en ella. |
| Importar bibliografía | Trabajo e informe de filas importadas, rechazadas y posibles duplicados. | Archivo y proveedor conservados; no atribuir lectura de PDF a una fila de metadatos. |
| Preparar búsqueda Scopus/WoS | Ecuación editable, campos, filtros, criterios, fecha y enlace oficial. | Persistir consulta reproducible sin API; ejecución manual del proveedor no se atribuye a TesisMCP. |
| Auditar afirmación/cita | Trabajo, versión del manuscrito, afirmaciones/citas y corpus permitido. | Resultado preliminar tipado con pasajes/localizadores; sin edición canónica hasta aceptación. |
| Invitar apoyo acotado | Tarea y lista de recursos/permisos autorizados. | Invitación expira/revoca; acceso a cada archivo/job vuelve a validar el grant. |
| Conectar/sincronizar Zotero | Estado de autorización, biblioteca y conflictos. | Credenciales solo en servidor; permisos mínimos y revocación. |
| Solicitar propuesta de IA | ID de trabajo y resultado tipado pendiente de revisión. | Contexto/versiones fijados; sin escritura directa de resultados canónicos. |
| Recalcular figura/exportar | Nueva vista o archivo con IDs de versiones de datos, texto y citas. | Operación reproducible, con errores visibles si faltan datos o permisos. |

Las rutas concretas deben conservar compatibilidad con las existentes de `backend/thesis/api/projects.py` y describirse en OpenAPI. Los casos anteriores son contratos de comportamiento, no afirmaciones de endpoints implementados.

- Mantener `/api/v1/` mientras se diseña una evolución compatible. Para cada operación nueva definir actor, proyecto, entrada tipada, precondiciones, salida, error estable, efecto transaccional e idempotencia.
- Toda lectura que pueda crecer debe paginarse: bibliotecas, resultados de búsqueda, citas, historial, extractos y trabajos.
- Las tareas lentas devuelven identificador/estado; el frontend puede consultar progreso y errores. No bloquear una petición HTTP durante OCR, extracción, búsqueda amplia o generación de capítulos.
- Guardar credenciales y datos sensibles en el servidor; el frontend recibe estados de conexión y permisos, nunca secretos. Registrar consentimiento para muestras de estilo y acceso a bibliotecas personales.
- Definir semántica de versiones para editor, método, fuentes, figuras, prompts y exportación antes de añadir nuevos modelos. Evitar copias independientes del mismo documento que no se puedan reconciliar.
- Al extender roles de asesor, mantener reglas de aprobación explícitas por proyecto. Una persona puede cumplir ambas funciones; ningún administrador/bibliotecario/experto externo debe volverse un rol obligatorio en todas las tesis.
- Los prompts y resultados externos son entrada no confiable. Validar esquema, enlaces a IDs del proyecto, hashes y nivel de evidencia antes de guardar; la IA no concede permisos ni cambia aprobaciones.

## 7. Entregas recomendadas para el backend

Usar como única secuencia vigente el [Plan de entregas y definición de terminado del backend](./plan_entregas_backend.md), que especifica B0–B10 y prioriza B5 tras la auditoría B0. Para B5 seguir el [contrato de recorrido y prompts configurables](./contrato_recorrido_y_prompts_configurables.md). El [criterio de backend listo para frontend](./criterio_backend_listo_para_frontend.md) define la salida final: B5 aislado no basta. Las tablas de entregas de planes históricos no son un roadmap paralelo. Una entrega vertical puede combinar filas si demuestra un recorrido completo y respeta sus dependencias. P01–P32 y capítulos 1–7 siguen como base compatible; las etapas empíricas y de cierre son alcance objetivo posterior.

## 8. Criterios de aceptación del primer trabajo de código

El primer agente desarrollador debe entregar un inventario por capacidad antes de proponer una migración. Para cada cambio implementado deberá poder mostrar:

1. Ruta y servicio existentes que reutilizó, o razón comprobable para crear uno nuevo.
2. Ejemplo de entrada/salida y errores de la operación web, con permisos y versión esperada.
3. Lectura de datos legados y reversibilidad de la migración, cuando cambie el esquema.
4. Una comprobación observable de que el tesista no puede modificar proyectos ajenos ni aprobaciones; el asesor no puede aprobar con observaciones abiertas.
5. Trazabilidad de cada cita/antecedente al registro y al nivel real de verificación. Los metadatos no se convierten automáticamente en lectura de texto completo.
6. Idempotencia o resolución explícita de conflictos en guardado, sincronización y trabajos en segundo plano.
7. Evidencia de que la capacidad nueva funciona en el recorrido web principal y no solo en una herramienta MCP o un script.
8. Actualización de esta guía/estado del producto con resultado real, límites y verificación ejecutada. No declarar completa una capacidad por existir una clase, ruta o mock.
9. Comparación de la instantánea aprobada, los comentarios del asesor y el contenido exportado: deben corresponder a la misma versión completa del capítulo.
10. En el flujo básico de Scopus/WoS se completa una búsqueda mediante ecuación/enlace y archivo exportado sin API ni credenciales guardadas por TesisMCP.
11. En la auditoría de cita se puede mostrar un pasaje localizado y una propuesta de corrección sin reemplazar silenciosamente texto ni referencia; con acceso solo a metadatos se informa que el contenido no fue verificado.
12. Si se activa un experto/bibliotecario, una prueba demuestra acceso solo al paquete compartido, respuesta vinculada a tarea/versión y ausencia de permisos de aprobación/edición no concedidos.

## 9. Decisiones técnicas que deben registrarse antes de su implementación

Están abiertas la representación exacta del documento del editor; la guía UTP y plantilla aplicable al piloto IEEE; el alcance de campos Zotero vivos en exportaciones; la política de varios asesores y firmas; el proveedor de IA para la web y tratamiento de muestras de estilo; la retención de PDF/datos privados; y las condiciones de Scopus/WoS. Estas decisiones no impiden auditar el código, diseñar contratos compatibles ni avanzar en importación y editor básico. Cualquier elección debe documentar alternativas, razón, impacto en datos existentes y forma de revertirla.
