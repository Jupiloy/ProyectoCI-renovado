# 🤖 GUÍA MAESTRA PARA AGENTES DE IA (TESISMCP)
> **Documento de Contexto Operativo y Reglas de Oro para Asistentes y Agentes de Código**  

**Alcance del prototipo acordado:** detener el recorrido antes de elaborar y aplicar instrumentos. P30–P32 no son obligatorios para la demostración; P26/P27 mencionan instrumentos previstos y deben decidirse en el recorrido concreto. Conservar pasos disponibles y recorridos editables, sin afirmar que se completa toda la tesis. IEEE es el estilo priorizado para el piloto; APA 7 sigue admitido por compatibilidad histórica. La web usará sesión Django; `GET /api/v1/auth/session/`, `POST /api/v1/auth/login/` y `POST /api/v1/auth/logout/` son los endpoints locales añadidos. El inicio requiere CSRF; no hay alta pública, recuperación ni CORS entre orígenes.
> **Proyecto:** TesisMCP — Asistente Metodológico de Tesis con Protocolo MCP y Circuito Determinista  
> **Institución:** Universidad Tecnológica del Perú (UTP) — Sede Piura | **Curso:** Curso Integrador 1 (2026)  
> **Destinatarios:** Claude Code, Cursor Agent, GitHub Copilot, Windsurf, Gemini CLI y agentes de los 5 integrantes del equipo.

---

## Ubicación y aislamiento de esta copia renovada

Esta carpeta nació como copia de trabajo `ProyectoCI-renovado`. El original local podía contener las versiones históricas `V1` y `version_espanol`; no asumir que existen en el clon de un integrante. La copia local conservó backend, MCP, frontend de referencia, documentación, `var/media`, `var/backups`, evidencia de recuperación, `var/models`, `var/tessdata` y `graphify-out`; **los elementos bajo `var/` están excluidos de Git y no llegarán al clonar**. Se conserva también el compilado frontend existente como artefacto histórico; no demuestra integración con el backend actual. Se omitieron los entornos/dependencias instalados (`.venv`, `node_modules`) y las carpetas históricas. El grafo copiado es un resultado histórico y puede contener rutas del proyecto original: regenerarlo desde esta carpeta antes de confiar en rutas o resultados actuales. `var/tessdata` conserva enlaces a archivos de Tesseract del sistema, por lo que necesita esos archivos en la máquina donde se use. La documentación y evidencias anteriores pueden referirse a rutas y comandos del original; son historia, no una orden de escribir en él. Varios scripts gráficos heredados escriben en `V1/docs/diagramas`: inspeccionarlos antes de ejecutarlos.

**Fuentes académicas:** los PDF de `docs/` están incluidos en la propuesta para compartirlos con el equipo. La puerta Grounded requiere los archivos en las rutas y con los nombres indicados por `core/grounding/audit_cli.py`. Antes de publicar el repositorio, revisar los permisos de redistribución de PDF, TXT derivados y demás materiales.

**Base de datos:** copiar archivos o clonar Git no crea ni clona PostgreSQL. Con los valores actuales, esta copia puede conectarse a la misma base `tesismcp` del proyecto original. No ejecutar migraciones ni escrituras desde dos copias suponiendo aislamiento. La media local sí es una copia separada; usar la misma base con ambas carpetas puede desincronizar referencias y archivos. Antes de trabajar de forma independiente, configurar una base y almacenamiento separados y restaurar una copia compatible. Los backups incluidos son sensibles y manuales; no son automáticos ni una copia fuera de este disco.

**Verificación de esta copia:** `TESISMCP_DB_CONTAINER=tesismcp-local-pg ./scripts/verify_podman.sh` terminó con 8/8 controles y 214 pruebas, exit code 0; 510.96 s de gate, 536.97 s incluido el build. Evidencia privada: `var/recovery/verificacion_copia.log` y `var/recovery/verificacion_copia.json`. Se verificó contra la base local existente; no constituye una prueba de aislamiento de PostgreSQL.

## 1. ¿De qué va este proyecto? (Resumen Ejecutivo)

**TesisMCP** es una plataforma web de acompañamiento metodológico, búsqueda documentada y producción asistida de borradores de tesis. Busca reducir la dispersión metodológica, las referencias no verificadas y la pérdida de observaciones entre tesistas y asesores.

**Para entender el estado y el objetivo sin confundirlos, leer en este orden:** [esta guía](./GUIA_AGENTE.md), [visión y decisiones de producto](./docs/01_vision_y_alcance/propuesta_integral_tesismcp_y_decisiones_de_diseno.md), [estado verificable del producto](./docs/07_desarrollo_prototipo/estado_version_producto.md) y, para desarrollar el backend, la [guía de la versión completa](./docs/02_arquitectura_y_sistema/guia_backend_version_completa_para_agentes.md) junto con su [paquete de especificación integral](./docs/02_arquitectura_y_sistema/especificacion_integral_backend.md), el [criterio de backend listo para frontend](./docs/02_arquitectura_y_sistema/criterio_backend_listo_para_frontend.md), el [contrato de recorrido y prompts configurables](./docs/02_arquitectura_y_sistema/contrato_recorrido_y_prompts_configurables.md) y la [especificación de búsqueda, lectura, revisión de citas y apoyos](./docs/02_arquitectura_y_sistema/especificacion_busqueda_y_revision_de_evidencia.md). La guía de arquitectura y el código describen lo implementado; los documentos de visión/especificación describen el producto objetivo.

### La Filosofía Arquitectural:
1. **La web es el producto principal.** El objetivo es que tesista y asesor trabajen en TesisMCP, incluido un editor enriquecido propio en el frontend con una experiencia familiar parecida a Word. Word y LibreOffice son formatos/herramientas de exportación o continuidad externa; Collabora Online queda fuera de la propuesta.
2. **El backend (`backend/thesis/`)** concentra reglas de dominio, estado académico, permisos, versiones y persistencia en Django + PostgreSQL. Web y MCP deben usar los mismos servicios y contratos; la IA no escribe directamente en la base de datos.
3. **BYOA es el flujo de IA objetivo:** la web inicia tareas mediante la API de TesisMCP; un conector las entrega al agente/runtime que vinculó el usuario; el agente analiza con el modelo disponible en su runtime y llama por MCP a las herramientas/datos autorizados de TesisMCP. El backend coordina jobs, identidad, permisos, estados y persistencia. MCP no es la API comercial del modelo ni, por sí solo, el despachador genérico de tareas de la web. El primer conector local BYOA para Antigravity CLI ya tiene endpoints, credenciales revocables por proyecto, claim/heartbeat/resultado y validación del job; la integración visual del frontend y una ejecución real de Antigravity todavía no están comprobadas; consultar [arquitectura BYOA, API y MCP](docs/02_arquitectura_y_sistema/arquitectura_byoa_api_mcp.md) y el [contrato del conector BYOA y adaptador Antigravity](docs/02_arquitectura_y_sistema/contrato_conector_byoa.md).
4. **P01–P32 y capítulos 1–7 son la base heredada implementada; el producto objetivo acompaña hasta el informe y la entrega.** No reducir la nueva arquitectura al MVP P01–P08 ni afirmar que las etapas empíricas posteriores ya existen. El recorrido y los prompts deben ser configurables por proyecto, con núcleo protegido y versiones. Se implementa por entregas tras inspeccionar el código existente; no reconstruir ni duplicar P01–P32 sin verificar.
5. **Zotero se integra; no se replica.** TesisMCP mantiene su editor y flujo de tesis, puede conectar la biblioteca Zotero con autorización y gestionar citas enlazadas a fuentes. No copiar la aplicación Zotero ni depender de Collabora. La compatibilidad de campos activos Zotero en DOCX solo se afirma después de probarla en un procesador compatible.
6. **El asesor** revisa revisiones identificables, ancla observaciones y aprueba o solicita cambios. Una persona puede cubrir funciones metodológicas y temáticas.
7. **Scopus/WoS no requieren API para el flujo base.** La plataforma ayuda a crear/guardar ecuaciones y abre la búsqueda oficial; el usuario la ejecuta y luego importa sus resultados. No describir como consulta automática lo que realizó el usuario manualmente.
8. **La revisión de citas compara afirmaciones con evidencia textual.** Metadatos válidos no prueban apoyo semántico. Mostrar pasajes/localizadores y nivel de acceso; cualquier reemplazo queda como propuesta hasta aceptación humana.
9. **Expertos y bibliotecarios pueden reducir trabajo con tareas acotadas.** Invitación a materiales y preguntas explícitas, con permisos limitados; no son roles universales ni reciben permiso de edición/aprobación. Administración institucional de normas se separa de las tesis privadas.

El frontend de `TesisMCP/` ya contiene acceso, selección de proyectos y editor por bloques. Su contrato HTTP se comprobó mediante Vite, Django y una base aislada; los clics y la apariencia en navegador todavía no se han comprobado porque Work tiene deshabilitado el navegador local. Consultar [el paso 2](docs/02_arquitectura_y_sistema/paso_2_documento_y_editor_versionado.md) antes de describirlo como capacidad operativa.

---

## 2. Analogía Rápida "Con Manzanitas"

Para que cualquier agente entienda el flujo sin perderse:
* **El Tesista:** El comensal que pide el menú y decide qué plato consumir.
* **El LLM (Cocinero talentoso pero alucinador):** Cocina rápido, pero si lo dejas solo inventa ingredientes falsos.
* **El Servidor MCP (El Mesero con comandas):** Solo acepta pedidos que encajen en fichas estrictas (`P01` a `P32`) y nunca deja que el cocinero toque la despensa.
* **Los Servicios Django (El Chef Ejecutivo y Auditor):** Revisa que el plato cumpla las normas antes de servirlo.
* **PostgreSQL + pgvector (La Despensa Blindada):** Base de datos con candados transaccionales y búsqueda vectorial local a costo cero.
* **El Trabajador en Segundo Plano (`run_document_worker`):** El cuarto de preparación pesada para tareas lentas (OCR, GROBID, embeddings).
* **El Asesor (El Inspector Sanitario):** Revisa el plato terminado y no puede firmar la aprobación si queda una sola observación abierta.

*(Para más detalles pedagógicos, leer [`docs/02_arquitectura_y_sistema/guia_arquitectura_con_manzanitas.md`](docs/02_arquitectura_y_sistema/guia_arquitectura_con_manzanitas.md)).*

---

## 3. Stack Tecnológico Real (Sin Alucinaciones)

| Capa | Tecnología | Versión / Detalle |
| :--- | :--- | :--- |
| **Lenguaje** | Python | `>= 3.12` |
| **Framework Backend** | Django + Django Ninja | Django 5.x, Django Ninja (OpenAPI en `/api/v1/docs`), Django Unfold (Admin) |
| **Base de Datos** | PostgreSQL 16 + `pgvector` | Imagen `docker.io/pgvector/pgvector:pg16` |
| **Servidor MCP** | SDK Oficial `mcp` | `mcp==2.3.0` (`from mcp.server.mcpserver import MCPServer`), transporte stdio local |
| **Búsqueda Vectorial** | FastEmbed | Modelo local `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dimensiones) |
| **Extracción Documental** | Poppler / OCRmyPDF / GROBID | `pdfinfo`, `pdftotext`, `tesseract-ocr`, GROBID 0.9.1 local |
| **Manuscritos DOCX** | python-docx / OOXML | Detección de campos de cita activos Zotero (`CSL_CITATION`) y Word |
| **Frontend web del tesista** | React + TypeScript + Vite en `TesisMCP/`; integración parcial | Acceso, proyectos y edición de bloques. Ida y vuelta HTTP real comprobada en base aislada; interacción visual y experiencia enriquecida completa pendientes. |
| **Pruebas** | pytest + pytest-django | Suite de integración contra PostgreSQL; ejecutar antes de declarar cambios listos |

---

## 4. Reglas de Oro Innegociables para Agentes de IA

Si estás generando o editando código en este proyecto, **DEBES cumplir estrictamente las siguientes reglas**:

### 🚫 Regla 1: Cero Tolerancia a Alucinaciones (Grounded Truth)
* **NUNCA inventes métricas, cifras o citas.** Si un porcentaje o valor $p$ no está literal en el texto original, no lo escribas.
* Diferencia matemáticamente **puntos porcentuales** de **variaciones relativas (%)**.
* Los conteos de páginas de PDFs deben ser físicos y reales (Poppler).
* Antes de dar por terminado cualquier cambio que involucre fuentes, ejecuta:
  ```bash
  python3 -m core.grounding.audit_cli
  ```
  Debe reportar **9/9 documentos verificados al 100%**.

### 🚫 Regla 2: Seguridad en el Protocolo MCP (Anti-Spoofing)
* **Las herramientas MCP NUNCA deben recibir un parámetro `user_id` o `correo` proporcionado por el modelo.**
* La identidad se resuelve exclusivamente en el backend desde la variable de entorno `TESISMCP_MCP_TOKEN` a través de [`mcp_server/django_bridge.py`](mcp_server/django_bridge.py).

### 🚫 Regla 3: Concurrencia Optimista Obligatoria (`lock_version`)
* Todo guardado de pasos metodológicos o ideas usa `select_for_update()` y compara `expected_version == profile.lock_version`.
* Si un cliente web y un cliente MCP guardan simultáneamente, el segundo debe recibir error de conflicto (`VersionConflictError`), nunca sobrescribir silenciosamente.

### 🚫 Regla 4: Integridad de Base de Datos e Inmutabilidad Académica
* En [`backend/thesis/models/__init__.py`](backend/thesis/models/__init__.py), las relaciones clave usan `on_delete=models.PROTECT`. Prohibido el borrado en cascada destructivo.
* Las revisiones de capítulos (`ChapterRevision`) y eventos de revisión (`ReviewEvent`) son inmutables en PostgreSQL.
* Un asesor **no puede aprobar** un capítulo si tiene observaciones en estado `OPEN`.

### 🚫 Regla 5: Convención de Nombres (Inglés vs. Español)
* **Código interno, base de datos y modelos:** Mantener en **inglés técnico** (`title`, `created_at`, `status`, `lock_version`) para interoperabilidad con Django.
* **Herramientas MCP, interfaces de usuario y mensajes de error:** En **español** (`crear_proyecto`, `guardar_paso`, `verbose_name="Título del proyecto"`).

### 🚫 Regla 6: No inventar acceso ni respaldo de citas
* Una búsqueda abierta manual no es una búsqueda ejecutada por backend. Guardar base, ecuación, filtros, fecha y archivo importado con su procedencia real.
* No exigir APIs para el recorrido base de Scopus/WoS. No guardar credenciales institucionales ni automatizar acceso autenticado en el flujo normal.
* DOI, título, resumen, número de citas o similitud vectorial no demuestran que la fuente apoye la afirmación. Evaluar respaldo exige texto inspeccionable y pasaje/localizador; si falta, registrar acceso insuficiente.
* La IA puede sugerir reemplazo o reformulación; no cambia el documento o citas canónicas sin aceptación explícita del tesista y el flujo de revisión aplicable.
* Un invitado recibe solo los materiales de una tarea aceptada; no adquiere acceso general, permiso de aprobación ni acceso a otros proyectos.

---

## 5. Mapa del Repositorio

```text
ProyectoCI/
├── backend/                        # Núcleo Django + Django Ninja
│   ├── config/                     # Configuración settings.py, urls.py, api.py
│   ├── thesis/
│   │   ├── models/                 # Modelos por dominio; __init__.py conserva thesis.models
│   │   ├── migrations/             # Corte B8 histórico 0044; BYOA añade 0045–0047
│   │   ├── admin.py                # Panel de asesor con Django Unfold
│   │   ├── services/               # Casos de uso puros (sin acoplamiento HTTP/LLM)
│   │   │   ├── steps.py            # Guardado transaccional P01-P32 / tarea configurable y lock_version
│   │   │   ├── workflows.py        # Recorrido configurable, prompts versionados y outputs USR_
│   │   │   ├── step_materializers/ # Registro y reglas por dominio para P01-P32
│   │   │   ├── step_contracts.py   # 32 contratos Pydantic estrictos (P01Output-P32Output, extra="forbid")
│   │   │   ├── reviews.py          # Máquina de estados FSM del asesor
│   │   │   ├── document_jobs.py    # Cola asíncrona de tareas pesadas
│   │   │   ├── search.py           # Búsqueda semántica sobre pgvector
│   │   │   └── mcp_auth.py         # Validación criptográfica de tokens MCP
│   │   ├── integrations/           # Adaptadores externos (OpenAlex, PDF, OCR, GROBID, DOCX)
│   │   ├── api/                    # Rutas REST Django Ninja (/api/v1/)
│   │   └── tests/                  # Pruebas automatizadas en pytest
│   └── manage.py                   # CLI Django (incluye run_document_worker e issue_mcp_token)
├── mcp_server/                     # Servidor MCP stdio (34 herramientas y 35 prompts)
│   ├── server.py                   # Instancia MCPServer y catálogo P01-P32
│   ├── project_tools.py            # Herramientas MCP de proyecto (@app.tool)
│   ├── prompts/                    # Plantillas P01-P32 y roles secuenciales del cliente LLM
│   ├── django_bridge.py            # Puente seguro hacia thesis.services
│   ├── demo/                       # Datos y utilidades de demostración
│   └── test_local.py               # Demostración E2E integral sobre transporte stdio con PDF real ARIA
├── core/grounding/                 # Capa de auditoría anti-alucinaciones de PDFs
├── scripts/                        # Scripts utilitarios (build_informe_ieee.py, etc.)
├── docs/                           # Documentación oficial y artefactos académicos
│   ├── 01_vision_y_alcance/        # Ficha técnica del proyecto
│   ├── 02_arquitectura_y_sistema/  # Arquitectura, modelo físico y diagramas_editables/
│   ├── 03_metodologia_y_prompts/   # Pasos P01 a P32, contratos y referencias_prompts/
│   ├── 04_modulo_investigacion_y_busqueda/ # Estrategia y matriz de antecedentes
│   ├── 05_modulo_colaborativo_asesor/      # Flujo de revisión y Django Unfold
│   ├── 06_informe_final_curso/     # Informe académico y versión IEEE histórica
│   └── 07_desarrollo_prototipo/    # Bitácora, pruebas, plan de 5 integrantes
└── AGENTS.md                       # Regla fundamental de Grounded Truth
```

### Organización de API y presentaciones del backend

`backend/thesis/api/projects.py` es la fachada que reexporta los routers, contratos y vistas existentes. `routers.py` define los routers compartidos; `schemas.py` concentra los esquemas de entrada; los módulos `routes_*.py` agrupan operaciones por dominio. Importar los módulos en el orden fijado por la fachada: modificarlo puede afectar la resolución de rutas. Los `operation_id` explícitos preservan los identificadores OpenAPI de la organización previa. El montaje sigue en `backend/config/api.py`. No crear rutas duplicadas ni asumir que reordenarlas es inocuo.

La validación de borradores está en `workflow_validation.py`; la ejecución y consulta de tareas personalizadas, en `workflow_execution.py`. `workflows.py` reexporta estas funciones y mantiene la creación, publicación y restauración del recorrido. Las transacciones y permisos se mantienen en los servicios; no crear una segunda implementación.

La representación de capítulos, recorridos, trabajos de IA y fuentes vive en `chapter_serialization.py`, `workflow_serialization.py`, `ai_job_serialization.py` y `source_serialization.py`. `chapter_queries.py` reúne consultas y catálogo por capítulo; `chapter_submission.py` contiene el envío transaccional y sus snapshots; `steps.py` conserva el guardado y reexporta las operaciones anteriores. `ai_job_context.py` construye y verifica el contexto; `ai_proposal_decisions.py` reúne el diff y las decisiones; `ai_jobs.py` conserva solicitud, procesamiento y worker, y reexporta los nombres anteriores. Los cuerpos y límites transaccionales se conservaron; esta reorganización no implica mejora de rendimiento ni cambios de modelo o migraciones.

### Estado actual de workflow y generación IA (26/10/2026)

- B5 ya añadió recorridos configurables con versiones, modos `LEGACY_SEQUENTIAL` y `CONFIGURABLE_GRAPH`, tareas personalizadas `USR_...` e historial `WorkflowTaskExecution` (migración `0020`). Ver [estado de producto](docs/07_desarrollo_prototipo/estado_version_producto.md) y [contrato B5](docs/02_arquitectura_y_sistema/contrato_recorrido_y_prompts_configurables.md).
- `POST /api/v1/projects/{project_id}/workflow/tasks/{task_id}/execute` guarda `output_data` recibido del cliente para tareas `USR_...`; no llama al proveedor LLM. La generación del backend sí existe en B5.1 mediante `AIGenerationJob`, worker y rutas de generar/consultar/cancelar/aceptar/rechazar.
- El flujo objetivo BYOA usa la web como panel: la API de TesisMCP crea/consulta tareas; un conector las entrega al agente del usuario; el agente ejecuta el modelo y usa el servidor MCP para herramientas/datos autorizados; el conector devuelve avances/resultados al backend para que la web los muestre. El conector local y el despacho básico ya están implementados mediante `run_byoa_connector`; la interfaz de usuario para vincularlo y una ejecución Antigravity real siguen pendientes de integración/verificación. B5.1 conserva además jobs server-side y un adaptador Gemini opcional, deshabilitado por defecto; una llamada real requiere credenciales y no está verificada. Ver [arquitectura BYOA, API y MCP](docs/02_arquitectura_y_sistema/arquitectura_byoa_api_mcp.md). No confundir esa vía opcional con BYOA ni duplicar adaptador, jobs o worker. B1+B2.2 ya añade documento canónico versionado; B1+B2.3 prepara vista previa tipada y aceptación versionada de P05/P29 hacia ese documento. No aplicar automáticamente otros outputs estructurados ni tareas `USR_...`. Consultar el [plan de entregas](docs/02_arquitectura_y_sistema/plan_entregas_backend.md) y el [paquete B1+B2.3](docs/02_arquitectura_y_sistema/paquete_b1_b2_3_diffs_ia_documento.md).
- Los documentos con cortes anteriores a 26/10/2026 pueden ser históricos. El código y las migraciones actuales prevalecen; confirmar símbolos y estado antes de programar.
- B3.1–B3.6 implementan fuentes multi-proveedor e importaciones manuales; B4.1–B4.5, citas estructuradas, revisión humana y Zotero de solo lectura sujeto a credenciales; B6.1–B6.4, lotes, worker, síntesis trazable e invitaciones acotadas. B7 quedó verificado: 52 modelos/40 migraciones. B8.1 añade datasets CSV/XLSX versionados; B8.2 añade tablas declarativas e inmutables. B8.3 agrega figuras PNG generadas desde tabla versionada, con hash, renderer y accesibilidad; B8.4 acepta nodos tipados de tabla/figura, valida su pertenencia/hash, congela versiones en el snapshot y las renderiza en el DOCX aprobado. Corte B8 histórico: 58 modelos y migraciones hasta `0044`; B8 completo pasó puerta integral 7/7, total 479.66 s, pytest 457.26 s, exit code 0 el 26/10/2026. El corte actual añade BYOA local mediante migraciones `0045`–`0047`: 59 modelos/47 migraciones según el verificador. BYOA no está incluido en aquella evidencia integral. Benchmark local B7: 9 PDF/971 páginas, muestra no representativa y sin medición de precisión OCR. No se verificaron corpus representativos/licencias, llamada Gemini real, OAuth Zotero real ni correo. Consultar [paquete B8](docs/02_arquitectura_y_sistema/paquete_b8_datos_figuras.md), [estado de producto](docs/07_desarrollo_prototipo/estado_version_producto.md) y [guía de continuidad](docs/02_arquitectura_y_sistema/guia_continuidad_backend.md).

---

## 6. Comandos Imprescindibles para el Agente

Antes de afirmar que una tarea o refactorización está lista, ejecuta en la terminal:

```bash
# 1. Comprobar que Django no tiene advertencias ni errores
DJANGO_DEBUG=1 .venv/bin/python backend/manage.py check

# 2. Comprobar que no hay modelos desincronizados sin migración
DJANGO_DEBUG=1 .venv/bin/python backend/manage.py makemigrations --check --dry-run

# 3. Ejecutar la suite automatizada (todas deben pasar en verde)
DJANGO_DEBUG=1 .venv/bin/pytest --reuse-db -q

# 4. Ejecutar la auditoría Grounded Anti-Alucinaciones
python3 -m core.grounding.audit_cli
```

---

## 7. Mapeo Rápido por Roles del Equipo (5 Integrantes)

Si el usuario te dice *"yo soy el Rol 3"* o *"trabajo en la base de datos"*, consulta su alcance:
* **Rol 1: Base de Datos & ORM:** Modelos en `backend/thesis/models/__init__.py`, migraciones, llaves `PROTECT`, índices pgvector.
* **Rol 2: Servidor MCP & Agente IA:** Herramientas en `mcp_server/project_tools.py`, puente `django_bridge.py`, cliente Cursor/Claude.
* **Rol 3: Validadores & API REST Ninja:** Reglas de validación en `step_contracts.py`, endpoints en `backend/thesis/api/projects.py`.
* **Rol 4: Panel del Asesor & Frontend:** Interfaz en `backend/thesis/admin.py` con `django-unfold`, revisión de observaciones y Swagger.
* **Rol 5: Calidad (QA), Pruebas y Word:** Pruebas en `backend/thesis/tests/`, mediciones de latencia, captura de evidencias para el informe final.

*(Plan completo en [`docs/07_desarrollo_prototipo/plan_trabajo_equipo_5_integrantes.md`](docs/07_desarrollo_prototipo/plan_trabajo_equipo_5_integrantes.md)).*

---

> 💡 **Nota para agentes:** Si tienes dudas de arquitectura o diseño, revisa siempre los archivos físicos en disco antes de deducir o inventar. El código en `backend/thesis/` y las pruebas en `tests/` son la fuente suprema de verdad.

### Operación local y recuperación (reparación posterior a B8)

La base local estaba en `0023` aunque el código llegaba a `0044`; fue respaldada junto con media, restaurada y migrada en un contenedor aislado antes de aplicar `0024`–`0044` a `tesismcp-local-pg`. No inferir estado de la base activa desde las pruebas de pytest. `scripts/verify_project.py` agrega `migrate --check --database default` como comprobación separada. Usar [el procedimiento y registro B10](docs/02_arquitectura_y_sistema/paquete_b10_operacion_local_y_despliegue.md), que distingue backups manuales, restore probado y automatización todavía pendiente. Herramienta canónica: `scripts/local_recovery.py`; no retomar el helper de `V1` como si respaldara archivos.
