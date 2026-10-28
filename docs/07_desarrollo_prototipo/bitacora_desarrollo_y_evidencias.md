# Bitácora de Desarrollo del Prototipo y Registro de Evidencias (TesisMCP)

> **Propósito de este documento:**  
> Servir como puente directo entre el código fuente del prototipo y el informe final en Word / IEEE (`docs/06_informe_final_curso/informe_academico_curso_integrador_IEEE.docx`).  
> Cada hito técnico implementado se registra aquí con sus payloads reales, capturas planificadas, endpoints probados y decisiones de diseño para que la redacción final sea un volcado directo de evidencias comprobadas.

> **Estado verificado al 18/10/2026:** 27 modelos de dominio, 18 migraciones, 34 herramientas MCP, 35 prompts y 59 pruebas recolectadas. Las cifras menores conservadas dentro de hitos anteriores describen el estado histórico de esos hitos; no representan el total actual.

---

## 1. Mapeo: ¿Qué partes del Word requerirán evidencia del prototipo?

| Sección del Word / IEEE | Evidencia Requerida del Prototipo | Fuente en el Código | Estado de Evidencia |
| :--- | :--- | :--- | :---: |
| **III. Metodología - Arquitectura Física** | Diagrama de componentes desplegados, configuración de base de datos PostgreSQL 16 con `pgvector` y Docker/Podman. | `backend/config/settings.py`, `compose.yaml` | 🟢 Listo / Verificado |
| **III. Metodología - Modelo de Datos** | Esquema relacional implementado, 18 migraciones Django aplicadas, 27 modelos en PostgreSQL, claves foráneas protegidas y reglas de inmutabilidad. | `backend/thesis/models/__init__.py`, `migrations/` | 🟢 Listo / Verificado |
| **III. Metodología - Protocolo MCP** | Herramientas implementadas (`@app.tool`), esquemas tipados, transporte stdio y puente con token `django_bridge.py`. | `mcp_server/server.py`, `project_tools.py` | 🟢 Listo / Verificado |
| **IV. Resultados - Implementación de Pasos P01 a P32** | Ejecución de pasos (Capítulos 1 al 7), contratos Pydantic con `extra="forbid"`, Strategy Registry (`step_materializers/__init__.py`), guardado atómico y `lock_version`. | `thesis/services/step_contracts.py`, `step_materializers/__init__.py`, `steps.py` | 🟢 Listo / Verificado |
| **IV. Resultados - Módulo de Revisión del Asesor** | Ciclo FSM (`DRAFT` -> `READY` -> `CHANGES_REQUESTED` -> `APPROVED`), observaciones ancladas y panel Unfold. | `thesis/services/reviews.py`, `admin.py`, API | 🟢 Listo / Verificado |
| **IV. Resultados - Pruebas de Software** | Suite local de 59 pruebas aprobadas con PostgreSQL; no mide aceptación de usuarios ni resultados académicos. | Suite de pruebas en `thesis/tests/` | 🟢 Listo / Verificado |
| **V. Discusión - Limitaciones Técnicas** | Blindaje contra alucinaciones con Zero-LLM (`UNVERIFIED_SOURCE` en P16), protección SSRF en PDFs, trabajador con `pg_try_advisory_lock`. | `integrations/pdf.py`, `document_jobs.py`, `steps.py` | 🟢 Listo / Verificado |

> 💡 **Explicación didáctica completa:** Consultar la [Guía de Arquitectura Explicada con Manzanitas](../02_arquitectura_y_sistema/guia_arquitectura_con_manzanitas.md) para entender el porqué y para qué de cada módulo mediante analogías cotidianas.

---

## 2. Registro Cronológico de Desarrollo (Sprint Prototipo)

### Hito 0: Servidor MCP Base (Completado)
* **Fecha:** 17 de Octubre de 2026.
* **Componente:** `mcp_server/server.py` y `mcp_server/test_local.py`.
* **Evidencia Comprobada:**
  - Servidor inicializado con SDK `mcp >= 2.0` (`MCPServer`).
  - Herramientas de catálogo metodológico (`estado_servidor`, `listar_pasos_mvp`, `consultar_detalle_paso`).
  - Ejecución de prueba inicial verificando payloads JSON estructurados.

---

### Hito 1: Backend Django + Modelos ORM y Migraciones (Completado)
* **Fecha:** 17 de Octubre de 2026.
* **Componente:** `backend/config/settings.py`, `backend/thesis/models/__init__.py` y `backend/thesis/migrations/`.
* **Evidencias Comprobadas:**
  - 18 migraciones generadas y aplicadas sin discrepancias (`python manage.py makemigrations --check --dry-run`).
  - 27 modelos de dominio creados en PostgreSQL con extensión `vector` (`pgvector:pg16`).
  - Restricciones de integridad referencial: `on_delete=models.PROTECT` para preservar inmutabilidad académica.
  - Verificación `manage.py check` con 0 errores de configuración.

---

### Hito 2: Servicios de Dominio, Pasos P01–P32 y Revisión Docente (Completado)
* **Fecha:** 17 de Octubre de 2026.
* **Componente:** `backend/thesis/services/` (`steps.py`, `step_contracts.py`, `reviews.py`, `document_jobs.py`).
* **Evidencias Comprobadas:**
  - Contratos metodológicos Pydantic estrictos para P01 a P32 (Capítulos 1 al 7: factibilidad, título, objetivos Bloom, preguntas ¿?, hipótesis, matriz de operacionalización, ecuaciones Scopus/IEEE, protocolo PRISMA, teorías base, constructos, metodología y banco de reactivos Likert).
  - Control de concurrencia optimista mediante `select_for_update()` y `lock_version`.
  - Semáforo y FSM del Asesor: prohibición estricta de aprobar capítulos con observaciones abiertas (`OPEN`).
  - Cola asíncrona de procesamiento de documentos (`DocumentJob`) y trabajador independiente (`run_document_worker`) con bloqueo consultivo PostgreSQL (`pg_try_advisory_lock`).

---

### Hito 3: Integración Bidireccional Servidor MCP <-> Base de Datos (Completado)
* **Fecha:** 17 de Octubre de 2026.
* **Componente:** `mcp_server/server.py`, `mcp_server/project_tools.py` y `mcp_server/django_bridge.py`.
* **Evidencias Comprobadas:**
  - 32 herramientas y pasos registrados en el catálogo metodológico oficial de MCP (`CATALOGO_PASOS`).
  - Seguridad reforzada: el cliente MCP no acepta `user_id` enviado por el LLM; la identidad se valida criptográficamente mediante el hash de `TESISMCP_MCP_TOKEN`.
  - Acceso unificado a: proyectos, pasos P01–P32 (Capítulos 1 al 7), búsqueda OpenAlex, extracción PDF por página física, OCRmyPDF, GROBID, búsqueda vectorial FastEmbed + pgvector, cotejo DOI Crossref y análisis DOCX Zotero/Word.

---

### Hito 4: Desacoplamiento Arquitectónico (Strategy + Registry) y Persistencia Relacional P09–P32 (Completado)
* **Fecha:** 18 de Octubre de 2026.
* **Componente:** `backend/thesis/services/step_materializers/__init__.py`, `backend/thesis/models/__init__.py` (migraciones `0016` y `0017`).
* **Evidencias Comprobadas:**
  - **Patrón Strategy + Handler Registry:** Extracción de la lógica de materialización fuera de `steps.py` hacia `step_materializers/__init__.py` con decorador `@register_step_handler` e inyección inmutable `StepExecutionContext`.
  - **Entidades Canónicas Persistidas:**
    - Capítulo 3: `ConsistencyRow` (ordinal 0 para general, 1..n para específicas), `ResearchVariable` (independiente y dependiente), `ConsistencyRowVariable` (cruces de matriz), `VariableDimension` e `Indicator`.
    - Capítulo 6: Persistencia canónica del enfoque (`QUANTITATIVE`, `QUALITATIVE`, `MIXED`) en `ResearchProfile.approach`.
    - Capítulo 7: `Instrument` (cuestionarios y entrevistas), `InstrumentItem` (banco de reactivos) e `InstrumentItemIndicator` (enlace formal a indicadores de P12).
  - **Pruebas automatizadas en ese hito:** la suite tenía 45 pruebas. El estado actual se verifica con 59 pruebas recolectadas.

---

### Hito 5: Simulación End-to-End del Servidor MCP con Fuente Real Verificada (Completado)
* **Fecha:** 18 de Octubre de 2026.
* **Componente:** `mcp_server/test_local.py`, `mcp_server/demo/support.py`, `mcp_server/demo/case_data.py`.
* **Evidencias Comprobadas:**
  - **Simulación Integral sobre Caso Semilla UTP Sede Piura:** Recorrido real mediante llamadas al SDK MCP (`app.call_tool`) desde `P01` hasta `P32` en PostgreSQL.
  - **Ingestión Real de PDF:** Sustitución del `RuntimeError` intencional por la carga de `INT1_ARIA_Multi_LLM_Framework_2025.pdf` (34 páginas físicas comprobadas, SHA-256 verificado y almacenamiento canónico en `var/media/sources/`).
  - **Validación Grounded en P16:** Comprobación estricta de `verification_level="TEXT_EXTRACTED_WITH_QUOTES"` y `paginas_reales=34`. Las tres citas requeridas se localizaron literalmente en el texto extraído de la página física indicada. Este nivel acredita extracción y coincidencia textual; no acredita por sí solo lectura crítica integral, autoría ni validez metodológica.
  - **Demostración Anti-Alucinación:** Intento de inyectar un paper alucinado bloqueado exitosamente con código `UNVERIFIED_SOURCE`.
  - **Ciclo Docente Completo:** 7 capítulos aprobados formalmente tras la resolución obligatoria de observaciones ancladas (`ADVISOR_UNRESOLVED_COMMENTS`).
  - **Resultado de la ejecución de demostración:** 32 pasos completados, 7 capítulos aprobados, 32 revisiones inmutables, 4 filas de consistencia, 8 cruces de variables, 4 dimensiones, 4 indicadores, 1 fuente con texto extraído y citas localizadas, 2 instrumentos con 8 reactivos y 14 eventos de auditoría docente. Son datos simulados del caso de demostración, no resultados de una prueba con usuarios.

---

### Hito 6: Búsqueda Federada Nacional/Local (ALICIA CONCYTEC + OpenAlex PE) y Modularización DDD (Completado)
* **Fecha:** 18 de Octubre de 2026.
* **Componente:** `backend/thesis/services/discovery_peru.py`, `backend/thesis/services/geography.py`, `backend/thesis/integrations/alicia.py`, `backend/thesis/models/`.
* **Evidencias Comprobadas:**
  - **Desacoplamiento Limpio de Modelos (DDD):** División del modelo monolítico en 7 submódulos relacionales (`accounts`, `projects`, `research`, `instruments`, `chapters`, `sources`, `documents`). El proyecto cuenta actualmente con 18 migraciones.
  - **Adaptador ALICIA CONCYTEC:** Se implementó el consumo del endpoint REST de búsqueda de ALICIA (`https://alicia.concytec.gob.pe/vufind/api/v1/search`) y su normalización a `METADATA_ONLY`. En la verificación actual, el comportamiento está cubierto con respuestas simuladas; no se certificó disponibilidad en vivo del servicio externo.
  - **Motor Geográfico Dinámico y Clasificación Explicable:** Resolución automática de jerarquías de provincias, distritos e instituciones por lugar del proyecto (`profile.place`), clasificando de forma determinista entre `LOCAL_POR_INSTITUCION`, `LOCAL_POR_OBJETO_ESTUDIO` y `NACIONAL`.
  - **Herramienta MCP Integrada:** Registro de `buscar_antecedentes_peru` bajo el protocolo MCP (`@app.tool`).
  - **Métrica histórica del hito:** en ese corte se registraron 48 pruebas. La cifra de líneas y archivos no se usa como métrica vigente porque cambia con cada edición. El estado actual contiene 59 pruebas recolectadas.

---

### Hito 7: Prompts con roles secuenciales (Completado)
* **Fecha:** 18 de Octubre de 2026.
* **Componente:** `mcp_server/prompts/` (`roles.py`, `hydration.py`, `catalog.py`, `templates/chapter_1.py` .. `chapter_7.py`), `backend/thesis/tests/test_mcp_prompts.py`.
* **Evidencias Comprobadas:**
  - **Secuencia de tres roles:** Un único cliente LLM sigue las instrucciones de *Asesor Metodológico*, *Investigador Grounded* y *Revisor de Contratos*. No se ejecutan agentes independientes.
  - **Inyección Dinámica de Contexto (Hidratación):** Lectura transparente del estado del proyecto en PostgreSQL (título, ODS, variables, indicadores, matriz de consistencia, `lock_version`) inyectada en el prompt antes de enviarlo al cliente MCP.
  - **Catálogo Completo Expuesto:** 35 prompts oficiales (32 metodológicos `P01`–`P32` + 3 prompts de rol dedicados) y 34 herramientas registradas en el servidor MCP (`server.py`).
  - **Verificación Automatizada:** Los ejemplos JSON se validan contra los contratos; la suite completa pasó 59 pruebas con PostgreSQL tras las correcciones.

---

### Hito 8: Interfaz web propia del tesista (Fuera del alcance acordado)
* **Alcance actual:** El tesista utiliza MCP o API. El asesor utiliza Django Admin/Unfold o la API de revisión; no está prevista una web propia del tesista.
* **Evidencias a extraer para el informe:**
  - [ ] Capturas del panel del asesor y del flujo MCP/API, obtenidas durante una prueba real.

---

## 3. Verificación y evidencias vigentes

### 3.1 Comandos oficiales

```bash
python3 -m core.grounding.audit_cli
DJANGO_DEBUG=1 .venv/bin/python backend/manage.py check
DJANGO_DEBUG=1 .venv/bin/python backend/manage.py makemigrations --check --dry-run
DJANGO_DEBUG=1 .venv/bin/pytest --reuse-db -q
DJANGO_DEBUG=1 .venv/bin/python mcp_server/test_local.py
```

La última suite completa registrada pasó 59 pruebas con PostgreSQL. La auditoría grounded pasó 9 de 9 documentos. El tiempo de ejecución no se fija como métrica permanente porque depende del equipo, caché y estado de la base.

### 3.2 Evidencias por rol

| Rol | Evidencia pendiente o renovable |
| :--- | :--- |
| 1. Datos | Captura actual de los 27 modelos/tablas de dominio y salida de migraciones. |
| 2. MCP | Listado del servidor con 34 herramientas y 35 prompts; ejecución desde un cliente real. |
| 3. Servicios/API | Swagger actual y casos de error de contrato, permisos y versión. |
| 4. Asesor | Panel Unfold con envío, comentario, resolución, aprobación y reapertura. |
| 5. QA | Salida completa de pytest, auditoría 9/9, demo P01–P32 y comprobación de enlaces Markdown. |

### 3.3 Límites de la evidencia

- La demo E2E usa datos metodológicos simulados; el PDF ARIA y sus extractos sí son archivos reales.
- Las pruebas de software no miden usabilidad, aceptación institucional ni calidad científica.
- P32 no demuestra una prueba piloto real mientras no se conserven datos de campo y cálculo reproducible.
- ALICIA se cubre mediante pruebas con respuestas simuladas; la disponibilidad externa debe comprobarse al desplegar.
- El borrador DOCX no equivale a una tesis institucional completa.

### Referencias cruzadas

- [Estado verificable del producto](./estado_version_producto.md)
- [Plan actual del equipo](./plan_trabajo_equipo_5_integrantes.md)
- [Protocolo de evaluación](./protocolo_evaluacion_experimental.md)
- [Modelo físico actual](../02_arquitectura_y_sistema/modelo_datos_fisico.md)
