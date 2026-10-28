# Backend de TesisMCP: proyectos, fuentes y borradores

Este código crea proyectos, valida y guarda los pasos P01–P32 (Capítulos 1 al 7), conserva revisiones y permite al asesor observar, pedir cambios y aprobar. También busca registros externos, incorpora PDF y localiza texto por página física. Los borradores DOCX se guardan aparte: Docling convierte el contenido a Markdown y un lector OOXML registra campos activos de Word y Zotero. PostgreSQL está verificado en desarrollo local; el despliegue público sigue pendiente. Una búsqueda externa devuelve **solo metadatos**; únicamente la incorporación o carga de una fuente puede producir extractos.

**Alcance objetivo:** completar la plataforma web TesisMCP para P01–P32, sin restringir el backend al MVP histórico P01–P08. El editor enriquecido propio del tesista aún está pendiente; BYOA es el flujo principal; ya existe el despacho local inicial a Antigravity CLI, aunque la interfaz del frontend y su ejecución real aún no están verificadas. MCP permite al agente usar herramientas/datos autorizados; no sustituye la API de tareas de la plataforma. Antes de añadir rutas, modelos o lógica, comprobar si la capacidad ya existe en el backend. Para las decisiones de producto, leer la [propuesta integral](../docs/01_vision_y_alcance/propuesta_integral_tesismcp_y_decisiones_de_diseno.md); para separar lo implementado de lo pendiente, consultar [estado del producto](../docs/07_desarrollo_prototipo/estado_version_producto.md).

Para el siguiente agente que programe el backend: consultar la [guía de desarrollo de la versión completa](../docs/02_arquitectura_y_sistema/guia_backend_version_completa_para_agentes.md) y el [paquete de especificación integral](../docs/02_arquitectura_y_sistema/especificacion_integral_backend.md), que enlaza inventario de brechas, contratos de dominio/API, cuentas/permisos, seguridad, decisiones abiertas y orden recomendado.

> 💡 **¿Quieres entender cómo funciona todo esto con analogías sencillas?**  
> Consulta la [Guía de Arquitectura Explicada con Manzanitas](../docs/02_arquitectura_y_sistema/guia_arquitectura_con_manzanitas.md), donde se detalla el porqué y para qué de cada componente (la base de datos, el mesero MCP, los contratos Pydantic, el trabajador en segundo plano y el semáforo del asesor).

## Sesión web para el prototipo

La API de proyectos usa la sesión autenticada de Django. El backend expone tres rutas para una interfaz web del mismo origen (o servida detrás de un proxy del mismo origen):

- `GET /api/v1/auth/session/`: consulta si hay sesión, devuelve los datos mínimos de la cuenta y entrega `csrf_token`.
- `POST /api/v1/auth/login/`: recibe JSON `{ "email": "...", "password": "..." }`; requiere enviar el token CSRF obtenido de la ruta de sesión en `X-CSRFToken`. La cookie de sesión se mantiene en el navegador.
- `POST /api/v1/auth/logout/`: invalida la sesión; requiere cookie y token CSRF.

**Selección de proyecto:** `GET /api/v1/projects?offset=0&limit=50` lista solo proyectos activos con membresía vigente del usuario. Devuelve `projects`, `offset`, `limit`, `has_more`; cada proyecto incluye `role` (`OWNER`/`ADVISOR`) y capacidades de lectura, edición documental, recorrido y revisión. El rol pertenece al proyecto; las acciones siguen autorizándose en servidor. `limit` admite de 1 a 100 y el orden es estable por nombre/UUID. Contrato y siguiente tarea de frontend: [paso 1 de acceso y selección](../docs/02_arquitectura_y_sistema/paso_1_acceso_y_seleccion_proyecto.md).

No existe registro público, invitación de cuenta, recuperación de contraseña ni verificación de correo en este flujo. Para el prototipo, un administrador crea cuentas desde Django Admin (`/admin/`) o se crea el primer superusuario con `createsuperuser`. `User` no guarda un rol académico global: el proyecto asigna `OWNER` (tesista) al crearse y el titular puede asignar por correo un asesor (`ADVISOR`) que ya tenga una cuenta activa. La asignación se hace con `POST /api/v1/projects/{id}/advisor`; no se crea automáticamente una cuenta para un correo desconocido. Las rutas no habilitan CORS ni autenticación entre dominios: en desarrollo el frontend debe usar un proxy al backend para mantener el mismo origen. Antes de uso por usuarios externos se deben añadir y evaluar limitación de intentos, recuperación de cuenta y configuración de dominio/HTTPS según el despliegue.

**Modelo de IA principal objetivo: BYOA con la web como panel de control.** La web crea jobs mediante la API de TesisMCP; un conector los entrega al agente/runtime vinculado por el usuario; el agente ejecuta el modelo disponible y llama las herramientas del servidor MCP para acceder a recursos autorizados. La API de TesisMCP coordina estado/resultados y MCP es la interfaz de herramientas del agente. No son la API comercial del modelo. El backend permite vincular una conexión Antigravity por proyecto, crear jobs BYOA y ejecutarlos con `run_byoa_connector`; `backend/thesis/agent_runtimes/` define el contrato intercambiable y registry, con Antigravity como único adaptador actual. No se verificó una ejecución real autenticada; la conexión visual del frontend sigue pendiente. Ver [arquitectura BYOA, API y MCP](../docs/02_arquitectura_y_sistema/arquitectura_byoa_api_mcp.md).

El código conserva B5.1 como vía opcional de generación directa desde jobs del backend usando un proveedor configurado en el servidor. Está deshabilitada por defecto, es distinta de BYOA y la llamada real no está verificada. Para el modo asíncrono de Compose, `TESISMCP_LLM_PROVIDER`, `TESISMCP_GEMINI_MODEL` y `GEMINI_API_KEY` se entregan solo a `ai_worker`; no se pasan al navegador ni son necesarios para BYOA. Solo si se habilita explícitamente una ejecución síncrona de desarrollo, el proceso web también necesitaría esa configuración. Usa [.env.example](../.env.example) como plantilla sin secretos y consulta el [paquete B5.1](../docs/02_arquitectura_y_sistema/implementacion_adaptador_gemini_b5_1.md).

**Alcance de la demostración acordado:** detener el recorrido antes de elaborar y aplicar instrumentos; P30–P32 no son obligatorios. P26/P27 mencionan instrumentos previstos, así que el recorrido de demo debe decidir si los incluye. Mantener los pasos y recorridos configurables disponibles.

## Estructura

| Carpeta | Responsabilidad |
| --- | --- |
| `config/` | Configuración Django, URLs y montaje de la API. |
| `thesis/models/` | Modelos por dominio y restricciones de PostgreSQL; `__init__.py` conserva las importaciones `thesis.models`. |
| `thesis/services/` | Casos de uso, permisos, versiones y autenticación MCP. |
| `thesis/integrations/` | Acceso a proveedores externos; OpenAlex es el primero. |
| `thesis/api/` | Adaptador HTTP con Django Ninja. |
| `../mcp_server/` | Adaptador MCP local sobre los mismos servicios. |

Los adaptadores no escriben SQL ni deciden permisos. Los servicios usan el ORM de Django; no se añade una capa de repositorios genéricos. Este es un monolito modular: se puede ampliar por dominio sin separar procesos prematuramente.

## Arranque local

Desde la raíz del proyecto:

```bash
uv pip install --python .venv/bin/python -r requirements-backend.txt
docker compose up -d db
export DJANGO_DEBUG=1
export DATABASE_URL='postgresql://tesismcp:tesismcp_local@127.0.0.1:5432/tesismcp'
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py createsuperuser
.venv/bin/python backend/manage.py runserver
```

En otra terminal, iniciar el trabajador documental con las mismas variables `DJANGO_DEBUG` y `DATABASE_URL`:

```bash
.venv/bin/python backend/manage.py run_document_worker
```

La carga de PDF local encola el conteo de páginas y la extracción de texto. La incorporación desde OpenAlex consulta primero los metadatos; si hay un enlace PDF permitido, encola su descarga y extracción. OCR, GROBID, indexación, cotejo DOI y conversión DOCX también usan la cola de PostgreSQL. Cuando se encola un trabajo, la respuesta incluye un objeto `job` con `job_id` y `status=QUEUED`; la API responde `202` en los casos indicados en sus rutas. `GET /api/v1/projects/{id}/jobs/{job_id}` permite consultar `QUEUED`, `RUNNING`, `SUCCEEDED` o `FAILED`, y el resultado o error correspondiente. La herramienta MCP `consultar_trabajo` ofrece el mismo estado. El trabajador procesa una operación a la vez; un bloqueo de PostgreSQL impide iniciar otro trabajador documental simultáneo. `run_document_worker --once` procesa como máximo un trabajo y termina. Si un trabajador se interrumpe, el siguiente recupera el trabajo pendiente, con un límite de intentos. La petición web no necesita que GROBID esté encendido para encolar, pero el trabajo fallará si sigue apagado cuando se ejecute. En equipos con poca memoria, ejecutar GROBID y el trabajador en un servidor separado.

Si el equipo usa Podman sin Compose, se puede iniciar la misma imagen con:

```bash
podman run -d --name tesismcp-local-pg -e POSTGRES_DB=tesismcp -e POSTGRES_USER=tesismcp -e POSTGRES_PASSWORD=tesismcp_local -p 127.0.0.1:5432:5432 -v tesismcp_postgres:/var/lib/postgresql/data docker.io/pgvector/pgvector:pg16
```

### Verificación automatizada con Podman

La suite requiere PostgreSQL real. `scripts/verify_podman.sh` reutiliza el contenedor local `tesismcp-local-pg`, construye una imagen efímera para las pruebas y ejecuta `scripts/verify_project.py` dentro de ella. En Linux, el contenedor de verificación usa la red del anfitrión para alcanzar el PostgreSQL ya publicado en `127.0.0.1:5432`; no necesita un proveedor Compose ni intenta iniciar un segundo contenedor de base de datos. Monta el proyecto bajo su misma ruta absoluta para que el verificador pueda resolver los enlaces `file://` de la documentación.

Desde la raíz del proyecto, con PostgreSQL en ejecución:

```bash
./scripts/verify_podman.sh
```

El script comprueba que el contenedor esté activo y que PostgreSQL responda antes de correr la puerta. La salida propaga el código de `scripts/verify_project.py`; `0` significa que pasaron las siete comprobaciones. El código fuente se monta en solo lectura, excepto el reporte JSON que la auditoría Grounded regenera. Se usa un `.venv` efímero y se desactiva la caché de pytest. Si el contenedor tiene otro nombre, define `TESISMCP_DB_CONTAINER`. La URL puede ajustarse mediante `TESISMCP_VERIFY_DATABASE_URL`.

La imagen de `compose.yaml` incluye pgvector y la migración activa la extensión `vector`. `indexar_fuente` crea embeddings locales de pasajes con el modelo multilingüe `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, que se descarga al primer uso en `var/models/fastembed/`. Después la inferencia es local. La búsqueda usa distancia coseno exacta filtrada por proyecto. Para extraer PDF se requieren `pdfinfo` y `pdftotext` de Poppler. Para escaneos se requieren OCRmyPDF, Tesseract y los idiomas correspondientes; `TESISMCP_OCR_LANGUAGES` usa `spa+eng` por defecto. Los archivos se guardan en `var/media/`, fuera del control de versiones. Para producción se exige `DJANGO_SECRET_KEY` y se configuran `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` y credenciales PostgreSQL propias. La descarga y extracción de PDF deben ejecutarse en un proceso aislado y con salida de red controlada antes de exponer el servicio públicamente.

En Debian/Ubuntu, instalar los paquetes de idioma `tesseract-ocr-spa` y `tesseract-ocr-eng` y comprobarlos con `tesseract --list-langs` antes de procesar PDF en español. Como alternativa sin permisos de administrador, colocar `spa.traineddata` y `eng.traineddata` en `var/tessdata/` y copiar o enlazar desde la instalación de Tesseract los directorios `configs/` y `tessconfigs/` (y `osd.traineddata` si se usa orientación automática). El adaptador usa esa carpeta cuando está presente. Estos datos de idioma son locales y `var/` está excluido del control de versiones. Si solo se dispone de inglés para una prueba local, establecer `TESISMCP_OCR_LANGUAGES=eng`.

La sesión web se inicia en `/admin/`; la API interactiva está en `/api/v1/docs`. Django Ninja comprueba CSRF en peticiones de escritura autenticadas con la sesión. Django Unfold muestra capítulos, revisiones y observaciones a asesores con acceso administrativo; sus acciones pueden aprobar o pedir cambios con las mismas guardas del servicio. La API ofrece el recorrido de revisión a asesores sin permiso administrativo. Las ediciones de proyectos y perfiles desde Admin se versionan con django-reversion; las entregas académicas usan `ChapterRevision` y `ReviewEvent`, que PostgreSQL impide modificar o borrar.

## Contenedores para desarrollo local

El perfil `app` de Compose levanta la API, el trabajador documental, el trabajador IA y PostgreSQL. La imagen usa Gunicorn para Django y WhiteNoise para los archivos estáticos del panel. `tesismcp_media` conserva PDF y DOCX; `tesismcp_models` conserva el modelo de embeddings. Antes del primer arranque hay que aplicar migraciones:

```bash
docker compose --profile app build
docker compose --profile app run --rm web python backend/manage.py migrate
docker compose --profile app up -d web worker
```

Con los valores predeterminados este perfil es **solo para desarrollo local** (`DJANGO_DEBUG=1`, puertos vinculados a `127.0.0.1`). Para exponerlo fuera del equipo hay que establecer `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY`, hosts y orígenes CSRF correctos, HTTPS y un proxy de confianza si se usa `DJANGO_TRUST_PROXY_SSL=1`. `GET /health/` responde `200` solo si Django puede consultar PostgreSQL. El almacenamiento documental de este despliegue es local y persistente; un servicio con disco efímero requiere almacenamiento compartido o un adaptador de objetos antes de procesar documentos en varias instancias.

## Pasos y revisión

`PUT /projects/{id}/steps/P01` a `P32` usa los contratos Pydantic definidos en `thesis/services/step_contracts.py`. Comprueba campos, límites y coherencia interna, aplica el orden de pasos y crea una revisión inmutable **asociada al paso guardado**. Se requiere `expected_version` e `idempotency_key` UUID. El contenido solo se persiste por acción del tesista; las comprobaciones de esquema no verifican la veracidad científica. El envío de capítulo (`POST /api/v1/projects/{id}/chapters/{no}/submit`) congela de forma transaccional un `ChapterSnapshot` inmutable (B1.1) con `sections_manifest`, outputs estructurados, hash SHA-256 canónico y protección por trigger PostgreSQL append-only. Los snapshots pueden consultarse en `GET /api/v1/projects/{id}/chapters/{no}/snapshots` y `.../snapshots/{snapshot_id}`. En B1.2 los comentarios de asesor identifican `snapshot_id`, validan offsets contra el texto congelado y las decisiones registran el snapshot en `ReviewEvent`; las aprobaciones nuevas usan `Chapter.approved_snapshot`. Las filas históricas sin snapshot siguen vinculadas a `revision`, y la base exige exactamente un ancla por comentario. B1.3 agrega `GET /api/v1/projects/{id}/chapters/{no}/export/approved.docx`, que genera un DOCX desde `approved_snapshot` y sus metadatos de procedencia. Solo admite aprobaciones vigentes ancladas a snapshot; no convierte outputs estructurados en prosa ni expone como actuales las aprobaciones históricas ligadas solo a revisión. El borrador `GET /api/v1/projects/{id}/export/draft.docx` conserva su semántica: reúne las últimas revisiones de pasos. Véanse las [especificaciones B1.1](../docs/02_arquitectura_y_sistema/paquete_b1_1_implementacion_snapshot.md), [B1.2](../docs/02_arquitectura_y_sistema/paquete_b1_2_revision_anclada_snapshot.md) y [B1.3](../docs/02_arquitectura_y_sistema/paquete_b1_3_exportacion_congelada_snapshot.md).

El editor backend tiene un documento canónico por capítulo (`ChapterDocument`) y revisiones inmutables (`ChapterDocumentRevision`) en un árbol JSON de bloques v1. `GET /api/v1/projects/{id}/chapters/{no}/document` devuelve esa revisión; si el capítulo solo tiene revisiones por pasos, devuelve una proyección legada de solo lectura. El titular guarda con `PUT` en la misma ruta, enviando `content_tree`, `expected_version` e `idempotency_key`. La proyección Markdown se conserva para interoperabilidad y comentarios actuales; no es el árbol canónico. Al enviar un capítulo, el snapshot v2 fija la revisión del documento. El DOCX aprobado usa el árbol congelado para snapshots v2 y mantiene el renderizado Markdown para snapshots históricos v1. Véase el [paquete B1+B2.2](../docs/02_arquitectura_y_sistema/paquete_b1_b2_2_documento_canonico.md).

B1+B2.3 añade `GET /api/v1/projects/{id}/ai-jobs/{job_id}/document-diff` para P05/P29. Devuelve una propuesta `REPLACE_DOCUMENT` con el árbol anterior, el propuesto, versión base, hash de salida y `proposal_sha256`; la consulta no escribe. Para aceptar esas tareas, `POST .../ai-jobs/{job_id}/accept` requiere `expected_document_version` y `proposal_sha256` de la vista previa revisada además de la versión de estado y `decision_key`. El servicio vuelve a calcular el diff dentro de la transacción; cualquier diferencia aborta el guardado. Una aceptación correcta conserva la `ChapterRevision` existente y crea una `ChapterDocumentRevision` con origen `AI_PROPOSAL`, enlazada desde `AIGenerationJob.result_document_revision`. Las salidas de otras tareas y `USR_...` no se aplican al árbol. Ver [paquete B1+B2.3](../docs/02_arquitectura_y_sistema/paquete_b1_b2_3_diffs_ia_documento.md).

El tesista puede vincular una afirmación con un fragmento exacto de un extracto que conserva página física y hash; el vínculo nace como `CANDIDATE`. El asesor asignado puede marcarlo `CONFIRMED` o `REJECTED`. La confirmación documenta su revisión de ese vínculo, no una garantía automática de verdad científica. PostgreSQL impide cambiar la procedencia y el texto de un vínculo ya creado.

P16 solo admite fuentes `TEXT_CHECKED` con conteo físico de páginas, archivo asociado y extractos localizados. Cada ficha requiere `metodologia_evidencia`, `muestra_evidencia` y `hallazgo_evidencia`, cada una con `excerpt_id` y `cita_textual`. El servicio exige que el texto citado aparezca en el extracto de esa fuente y guarda `pagina_fisica`; devuelve `TEXT_EXTRACTED_WITH_QUOTES`. Esto acredita localización textual, pero todavía exige revisión humana de portada, autoría y de si cada pasaje respalda la afirmación. P20 admite `IEEE` para el piloto y conserva `APA_7` por compatibilidad; el editor canónico tiene desde B4 un flujo independiente de citas IEEE estructuradas, todavía preliminar. `GET /api/v1/projects/{id}/export/draft.docx` genera un Word editable con las últimas revisiones guardadas, identificado como borrador; aplica A4, Arial 11, interlineado doble y márgenes de la [Guía del Egresado UTP v14, Anexo 15](https://www.utp.edu.pe/web/sites/default/files/2026-05/Guia_del_egresado_Pregrado_V14_PT.pdf). No incorpora carátula completa ni reporte de similitud porque faltan datos y archivos específicos; tampoco certifica la validez de las citas.

## Citas estructuradas, IEEE preliminar y Zotero (B4)

El documento canónico admite marcas `citations` por bloque de párrafo en `PUT /api/v1/projects/{id}/chapters/{no}/document`. Cada marca conserva grupo, posición, fuente del proyecto y localizador; el backend congela metadatos en la revisión. `GET /api/v1/projects/{id}/chapters/{no}/citations/ieee` devuelve numeración por primera aparición y bibliografía genérica preliminar. No es una validación editorial IEEE completa por tipo documental. El snapshot aprobado congela el manifest y el DOCX aprobado inserta las marcas/referencias desde ese snapshot; el borrador DOCX conserva su semántica anterior.

La evidencia enlaza una afirmación con un pasaje de la misma fuente `TEXT_CHECKED`, con offsets, página y hashes. Los metadatos Crossref, el estado de texto extraído y la revisión semántica humana son señales diferentes. `automated_semantic_assessment` informa `NOT_PERFORMED`; el asesor puede registrar `SUPPORTS`, `CONTRADICTS`, `UNRELATED` o `INSUFFICIENT`. La sustitución de cita se presenta como propuesta y solo una aceptación explícita del titular crea una nueva revisión canónica.

La conexión Zotero usa OAuth 1.0a de lectura a biblioteca personal. Para prepararla localmente, copia `.env.example` a `.env`, registra una aplicación Zotero con callback exacto `http://127.0.0.1:8000/api/v1/integrations/zotero/callback`, rellena `ZOTERO_OAUTH_CLIENT_KEY` y `ZOTERO_OAUTH_CLIENT_SECRET`, y genera una clave Fernet persistente para `ZOTERO_CREDENTIAL_ENCRYPTION_KEY` (por ejemplo, con `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`). Compose entrega estas variables solo al servicio web. Inicia sesión en TesisMCP y abre `GET /api/v1/integrations/zotero/connect` para autorizar. La API key de usuario se cifra en base de datos. El sistema puede listar e importar registros como `UNVERIFIED_METADATA`; no descarga adjuntos, no escribe en Zotero y no crea campos Zotero activos en el DOCX. Al desconectar intenta revocar remotamente; si falla, elimina la copia local e indica la página de revocación manual. La autorización OAuth real no está probada hasta configurar esas credenciales.

El mapa de rutas, payloads, roles, migraciones y límites está en [implementación B4](../docs/02_arquitectura_y_sistema/implementacion_b4_citas_ieee_zotero.md). P20 prioriza IEEE para el piloto y conserva `APA_7` por compatibilidad; su lista es independiente de las citas estructuradas del editor y no verifica el formato de cada referencia. La preparación local no demuestra que OAuth funcione hasta completar una autorización real.

## Lotes, worker, síntesis e invitaciones de apoyo (B6.1–B6.4)

`POST /api/v1/projects/{id}/ai-batches` crea de forma atómica un lote de 1–8 tareas distintas del workflow publicado, reutilizando un `AIGenerationJob` por tarea. Requiere `tasks` (cada una con `task_id`, `input_data?`, `context_refs?`), `expected_state_version`, `workflow_version_no` e `idempotency_key`. Solo el titular puede crear y cancelar; participantes autorizados pueden consultar. `GET /api/v1/projects/{id}/ai-batches` lista hasta 50 lotes y `GET .../ai-batches/{batch_id}` consulta estados individuales, agregado, `status_counts` y `completed_count`. `POST .../ai-batches/{batch_id}/cancel` cancela solo jobs `QUEUED`, deja intactos los que ya corren y reporta conteos. El resultado exitoso sigue siendo una propuesta B5.1 con aceptación individual; no hay fusión ni inserción masiva en el manuscrito. Si `TESISMCP_SYNC_AI_GENERATION=True`, la creación falla con `ASYNC_GENERATION_REQUIRED` para impedir llamadas al proveedor dentro de la transacción.

B6.2 hace el reclamo de jobs atómico y permite configurar `TESISMCP_AI_WORKER_CONCURRENCY` en Compose (predeterminado 1) hasta `TESISMCP_AI_WORKER_MAX_CONCURRENCY` (predeterminado 4). También se puede ejecutar `python backend/manage.py run_ai_worker --concurrency 2`; `--once` solo admite concurrencia 1. El worker mantiene un único advisory lock global y usa hilos en un proceso. Al iniciar, los jobs que quedaron `RUNNING` se marcan `FAILED/WORKER_INTERRUPTED`, no se reintentan automáticamente por el riesgo de duplicar una llamada facturable. La cola común procesa tanto generación como síntesis, eligiendo por antigüedad; esta concurrencia no configura un límite de gasto monetario.

B6.3 permite solicitar una síntesis de 2–8 jobs `SUCCEEDED` del mismo lote. La respuesta se genera bajo esquema estricto, con hashes y referencias a task_id del snapshot; el titular la puede aceptar/rechazar como **informe auxiliar**. No se inserta en `ChapterDocument`, no acepta los jobs fuente y no equivale a aprobación académica. API: `POST/GET /api/v1/projects/{id}/ai-batches/{batch_id}/syntheses`, `GET .../{synthesis_id}`, `POST .../{synthesis_id}/cancel` y `POST .../{synthesis_id}/decision`.

B6.4 permite al titular o asesor asignado invitar una cuenta activa existente a una tarea publicada y fuentes explícitas. El invitado acepta con token cuya versión plana solo se entrega una vez y cuyo SHA-256 se persiste; consulta únicamente la tarea, extractos concedidos y PDF compartido con hash verificado. Puede registrar una respuesta textual append-only con referencias a extractos. No se vuelve `ProjectParticipant`, no edita manuscrito, no aprueba ni invita. El token debe compartirse manualmente: este bloque no implementa alta de cuentas ni envío de correo. API: `POST/GET /api/v1/projects/{id}/support-invitations`, `POST .../{invitation_id}/revoke`, `GET .../{invitation_id}/contributions`; aceptación, espacio, archivo y aporte bajo `/api/v1/projects/support-invitations/{invitation_id}/...`.

La migración `0037_projectsupportinvitation_supportcontribution_and_more.py` añade cuatro modelos y triggers de integridad. Ver [paquete B6 completo](../docs/02_arquitectura_y_sistema/paquete_b6_completo.md), [B6.3](../docs/02_arquitectura_y_sistema/paquete_b6_3_sintesis_trazable.md) y [B6.4](../docs/02_arquitectura_y_sistema/paquete_b6_4_invitaciones_apoyo.md). La puerta integral B6 completa pasó 7/7, 395.34 s, exit code 0; la suite pytest pasó en 374.20 s.

## Conector BYOA local para Antigravity

El backend permite vincular una conexión por proyecto con `POST /api/v1/integrations/agents` (sesión Django + CSRF), listar mediante `GET /api/v1/integrations/agents?project_id=...` y revocar mediante `DELETE /api/v1/integrations/agents/{connection_id}`. La creación requiere que el usuario sea titular del proyecto y devuelve una sola vez `connector_token` y `mcp_token`; la respuesta lleva `Cache-Control: no-store`. En base de datos solo se guardan hashes. Cada conexión dura hasta 30 días, se puede revocar y queda limitada a un proyecto.

Al solicitar una propuesta, usa la ruta existente `POST /api/v1/projects/{project_id}/workflow/tasks/{task_id}/generate` con `execution_mode: "BYOA"` y el `agent_connection_id` del mismo proyecto, además de las entradas/idempotencia/versiones habituales. El backend conserva el contexto y esquema congelados. El job queda pendiente hasta que el conector lo reclame. Los jobs `SERVER` permanecen separados y el worker Gemini no reclama jobs BYOA.

El conector local usa `TESISMCP_API_BASE_URL`, `TESISMCP_CONNECTOR_TOKEN`, `TESISMCP_MCP_TOKEN`, `DATABASE_URL` y, opcionalmente, `TESISMCP_RUNTIME_EXECUTABLE`, `TESISMCP_RUNTIME_MODEL`, `TESISMCP_RUNTIME_EFFORT` (o los alias `TESISMCP_AGY_*`). Arráncalo desde la raíz del repositorio con `DJANGO_DEBUG=1 .venv/bin/python backend/manage.py run_byoa_connector`. Acepta `--once` para procesar como máximo un trabajo. El runtime se selecciona con `--runtime` o `TESISMCP_RUNTIME` y el ejecutable con `--runtime-path` o `TESISMCP_RUNTIME_EXECUTABLE`; las variables antiguas `TESISMCP_AGY_PATH` y `TESISMCP_AGY_MODEL` siguen aceptadas para Antigravity. Para añadir otro agente implementa `AgentRuntimeAdapter`, registra su código en `agent_runtimes/registry.py` y adapta su configuración MCP; no basta con cambiar el nombre del proveedor. Fuera de localhost exige HTTPS. El conector usa Antigravity CLI headless `stream-json`, recibe su esquema JSON y guarda la configuración MCP en un directorio temporal con permisos privados; no modifica la configuración global. Si encuentra una entrada global de TesisMCP, crea un override temporal deshabilitado y usa una conexión limitada al proyecto con solo herramientas MCP de lectura.

Antigravity CLI aplica sus permisos a MCP. Si no están autorizadas las herramientas del servidor temporal, el modo headless puede denegarlas sin detener la ejecución; configura explícitamente `mcp(tesismcp-byoa/*)` en `permissions.allow` de `~/.gemini/antigravity-cli/settings.json`. El conector detecta el mensaje `soft-denied` y marca el job fallido para evitar presentar una salida que aparenta haber consultado herramientas. No uses `--dangerously-skip-permissions`. La cancelación desde la web se comunica al proceso en su siguiente heartbeat. Los leases vencidos se marcan fallidos sin reintento automático para no duplicar una ejecución/costo.

La salida se valida de nuevo en Django contra el contrato Pydantic/JSON Schema, se guarda como propuesta pendiente de aceptación y no cambia automáticamente el capítulo. La procedencia de modelo/conversación es declarada por el runtime, no una atestación criptográfica. La ejecución real requiere instalar y autenticar `agy`; no se afirma que esté probada en este repositorio. Para el contrato común y los límites de seguridad, consulta [BYOA y Antigravity](../docs/02_arquitectura_y_sistema/contrato_conector_byoa.md).

## Herramientas MCP locales

Después de crear un usuario activo, emitir un token:

```bash
.venv/bin/python backend/manage.py issue_mcp_token ana@example.org
```

El comando muestra la credencial una sola vez. Configurarla en `TESISMCP_MCP_TOKEN` para el proceso MCP y ejecutar `.venv/bin/python -m mcp_server.server`. La base solo almacena su hash. El token caduca y puede revocarse desde Django Admin. Nunca pasar `user_id` ni el correo como parámetro de una herramienta para elegir la identidad.

Herramientas conectadas a Django: `crear_proyecto`, `obtener_estado`, `registrar_idea`, `explorar_idea`, `incorporar_fuente_openalex`, `listar_fuentes` y `consultar_extractos`. Las herramientas anteriores del catálogo siguen disponibles. `registrar_idea` requiere `expected_version` para detectar ediciones concurrentes. `explorar_idea` devuelve preguntas de orientación si todavía no hay idea; cuando sí la hay, consulta OpenAlex y etiqueta todos los trabajos como `METADATA_ONLY`.

`listar_borradores`, `consultar_borrador` y `consultar_citas_borrador` exponen por MCP los borradores cargados mediante la API. El texto y las citas se consultan por tramos para limitar la respuesta al cliente. Sus campos de cita aún no están verificados contra fuentes externas.

Para análisis bibliográfico de PDF, iniciar GROBID local con `docker compose --profile grobid up -d grobid` o `podman run -d --name tesismcp-grobid -e JAVA_OPTS='-Xms256m -Xmx1024m -XX:ActiveProcessorCount=2' -p 127.0.0.1:8070:8070 docker.io/grobid/grobid:0.9.1-crf`. En equipos con más recursos, el límite JVM se puede ajustar. `TESISMCP_GROBID_URL` apunta por defecto a `http://127.0.0.1:8070`; solo se admiten destinos locales. `analizar_fuente_grobid` encola el análisis; el trabajador guarda el TEI y las referencias extraídas como datos automáticos. `indexar_fuente` encola la generación de vectores y `buscar_pasajes` consulta pgvector; ninguno altera el estado de verificación científica de la fuente.

## API

| Método y ruta | Acción |
| --- | --- |
| `POST /api/v1/projects` | Crea proyecto y titular; `title` es opcional mientras se explora el tema. |
| `GET /api/v1/projects/{id}` | Consulta el estado autorizado. |
| `PUT /api/v1/projects/{id}/idea` | Guarda idea provisional con versión esperada. |
| `GET /api/v1/projects/{id}/idea/explore` | Busca metadatos en OpenAlex. |
| `GET /api/v1/projects/{id}/discovery/semantic-scholar?query=...` | Busca metadatos en Semantic Scholar; no registra ni verifica fuentes. |
| `GET /api/v1/projects/{id}/discovery/peru?query=...` | Busca ALICIA/artículos con filiación peruana; devuelve metadatos y clasificación local/nacional sin certificar revisión por pares. |
| `GET /api/v1/projects/{id}/export/draft.docx` | Descarga un borrador Word con el texto guardado de cada paso. |
| `GET /api/v1/projects/{id}/chapters/{chapter_no}/export/approved.docx` | Descarga un DOCX desde el snapshot vigente aprobado del capítulo. |
| `POST /api/v1/projects/{id}/advisor` | Asigna un asesor existente al proyecto del titular. |
| `GET /api/v1/projects/advisor/dashboard` | Lista proyectos y estados de capítulos del asesor autenticado. |
| `PUT /api/v1/projects/{id}/steps/{step_code}` | Valida y guarda P01–P32 (Capítulos 1 al 7) con versión e idempotencia. |
| `GET /api/v1/projects/{id}/chapters/{chapter_no}` | Consulta progreso y revisión vigente. |
| `POST /api/v1/projects/{id}/chapters/{chapter_no}/submit` | Envía un capítulo completo al asesor. |
| `POST/GET /api/v1/projects/{id}/chapters/{chapter_no}/comments` | Crea o lista observaciones ancladas. |
| `POST /api/v1/projects/{id}/comments/{comment_id}/resolve` | El asesor resuelve una observación. |
| `POST /api/v1/projects/{id}/chapters/{chapter_no}/decision` | Solicita cambios, aprueba o reabre. |
| `POST /api/v1/projects/{id}/sources` | Consulta un ID OpenAlex; si hay un PDF permitido, encola su descarga y extracción y devuelve `202` con `job`. Si no lo hay o está retractado, devuelve la ficha sin trabajo. Cuerpo: `{"openalex_id":"W..."}`. |
| `POST /api/v1/projects/{id}/sources/upload` | Conserva un PDF del titular y encola el conteo físico y la extracción; devuelve `202` con `job` cuando queda pendiente. Usa `multipart/form-data`: campos `label` y `file`. |
| `POST /api/v1/projects/{id}/sources/import-bibliography` | Importa RIS/BibTeX/CSV del titular con `multipart/form-data` (`provider`, `file`). Guarda el origen declarado, huella del archivo e identidad del registro; marca posibles duplicados para revisión sin fusionarlos. No consulta Scopus/WoS ni verifica la portada. |
| `POST /api/v1/projects/{id}/sources/import-bibliography` con `execution_id` opcional | Relaciona cada fila importada con esa ejecución mediante vínculos históricos inmutables que conservan el hash de la exportación. No verifica que el archivo proceda realmente de la base declarada. |
| `POST /api/v1/projects/{id}/sources/select-discovery` | Guarda un resultado seleccionado de OpenAlex, Semantic Scholar o ALICIA, con metadatos recibidos del cliente y etiquetados como no verificados. Puede asociarlo a una ejecución; no reconsulta el proveedor, descarga PDF ni fusiona duplicados. |
| `POST /api/v1/projects/{id}/sources/duplicate-decisions` | El titular guarda una decisión inmutable y versionada sobre dos fuentes coincidentes: `MARK_DUPLICATE`, `KEEP_SEPARATE` o `SET_PRIMARY` con `primary_source_id`. No elimina, fusiona ni migra citas. |
| `GET /api/v1/projects/{id}/sources/duplicate-decisions` | Participantes autorizados consultan el historial de decisiones y la decisión vigente por par. |
| `GET /api/v1/projects/{id}/search-strategies/{strategy_id}/executions/{execution_id}/sources` | Consulta las fuentes y hashes enlazados a una ejecución; requiere que esta pertenezca a la estrategia y proyecto indicados. |
| `POST /api/v1/projects/{id}/search-strategies` | Crea estrategia bibliográfica versionada e inmutable; valida proveedor, límites y URL HTTPS (dominio oficial al elegir Scopus/WoS). |
| `GET /api/v1/projects/{id}/search-strategies` | Lista la última versión de cada estrategia del proyecto para participantes autorizados. |
| `GET /api/v1/projects/{id}/search-strategies/{strategy_id}` | Consulta el historial completo de versiones de la serie identificada. |
| `POST /api/v1/projects/{id}/search-strategies/{strategy_id}/revisions` | Crea una revisión inmutable con `expected_version` e idempotencia; titular únicamente. |
| `POST /api/v1/projects/{id}/search-strategies/{strategy_id}/executions/manual` | Guarda una declaración manual del titular, con fecha, número opcional de resultados y notas. No verifica el acceso ni ejecuta Scopus/WoS. |
| `GET /api/v1/projects/{id}/search-strategies/{strategy_id}/executions` | Lista las declaraciones manuales asociadas a esa versión exacta. |
| `GET /api/v1/projects/{id}/sources` | Lista las fuentes y su nivel de inspección. |
| `GET /api/v1/projects/{id}/sources/{source_id}/excerpts` | Devuelve extractos con página física y hash; admite `page_no` y `limit`. |
| `POST /api/v1/projects/{id}/sources/{source_id}/ocr` | Encola OCR para un PDF en `OCR_REQUIRED`. |
| `POST/GET /api/v1/projects/{id}/sources/{source_id}/doi-check` | Encola o consulta metadatos DOI de Crossref. |
| `POST /api/v1/projects/{id}/sources/{source_id}/locate` | Localiza texto candidato con página física y hash. |
| `POST/GET /api/v1/projects/{id}/evidence-links` | Crea o lista vínculos candidato entre afirmación y extracto. |
| `POST /api/v1/projects/{id}/evidence-links/{link_id}/review` | El asesor confirma o rechaza el vínculo. |
| `POST /api/v1/projects/{id}/sources/{source_id}/grobid` | Encola la extracción TEI y bibliografía; devuelve `202` y `job_id`. |
| `GET /api/v1/projects/{id}/sources/{source_id}/grobid` | Consulta referencias extraídas, con `offset` y `limit`. |
| `POST /api/v1/projects/{id}/sources/{source_id}/index` | Encola la generación de embeddings; devuelve `202` y `job_id`. |
| `GET /api/v1/projects/{id}/jobs/{job_id}` | Consulta estado, resultado y error del trabajo autorizado. |
| `POST /api/v1/projects/{id}/passages/search` | Busca candidatos semánticos: `{"query":"...","limit":5}`. |
| `GET /api/v1/projects/{id}/workflow` | Consulta estado de recorrido del proyecto (versión publicada, borrador, diff, `lock_version`). |
| `PUT /api/v1/projects/{id}/workflow/draft` | Crea o modifica borrador de recorrido (orden, tareas opcionales, dependencias, prompts) con concurrencia optimista (`expected_version`). |
| `POST /api/v1/projects/{id}/workflow/validate` | Valida borrador (detección de ciclos por DFS y protección estricta de `P04`, `P16`, `P20`, `P28`). |
| `POST /api/v1/projects/{id}/ai-batches` | Crea atómicamente hasta 8 jobs independientes en un lote (`202`). |
| `GET /api/v1/projects/{id}/ai-batches` | Lista hasta 50 lotes del proyecto. |
| `GET /api/v1/projects/{id}/ai-batches/{batch_id}` | Consulta estado agregado derivado y estado por tarea. |
| `POST /api/v1/projects/{id}/ai-batches/{batch_id}/cancel` | Cancela únicamente los jobs del lote que sigan `QUEUED`. |
| `POST /api/v1/projects/{id}/workflow/publish` | Publica borrador como versión inmutable activa y activa el modo `CONFIGURABLE_GRAPH`. |
| `POST /api/v1/projects/{id}/workflow/restore` | Restaura versión histórica previa creando una nueva versión publicada inmutable. |
| `GET /api/v1/projects/{id}/workflow/tasks/{task_id}/prompt` | Obtiene el prompt efectivo y contextualizado de una tarea en el proyecto. |
| `POST /api/v1/projects/{id}/workflow/tasks/{task_id}/generate` | Solicita generación asistida con IA de una tarea (`202` encolada / `200` sincrónica); genera una propuesta pendiente de aceptación. |
| `GET /api/v1/projects/{id}/ai-jobs/{job_id}` | Consulta estado, resultado y errores del trabajo de generación IA. |
| `POST /api/v1/projects/{id}/ai-jobs/{job_id}/cancel` | Cancela un trabajo de generación en cola (`QUEUED`). |
| `POST /api/v1/projects/{id}/ai-jobs/{job_id}/accept` | Acepta explícitamente la propuesta e incorpora como revisión canónica (`save_step` en P01–P32 o `WorkflowTaskExecution` en `USR_...`). P05/P29 usan el campo tipado `contenido_markdown` como texto de revisión; otros outputs no se interpretan como prosa. |
| `POST /api/v1/projects/{id}/ai-jobs/{job_id}/reject` | Rechaza explícitamente la propuesta sin alterar el manuscrito ni el perfil. |
| `POST /api/v1/projects/{id}/manuscripts/upload` | Conserva un DOCX y encola conversión; `multipart/form-data`: `label` y `file`. |
| `GET /api/v1/projects/{id}/manuscripts` | Lista borradores autorizados. |
| `GET /api/v1/projects/{id}/manuscripts/{manuscript_id}` | Devuelve Markdown y campos de cita detectados. |

El DOCX original se conserva con hash SHA-256. Se aceptan campos `CITATION` de Word y `ZOTERO_ITEM CSL_CITATION` de Zotero en el cuerpo, notas al pie y notas finales. La salida separa el texto presentado, el código del campo y los identificadores o localizadores declarados por Zotero. Una cita escrita como texto corriente no se identifica como campo activo. Los marcadores de cita de tipo *bookmark*, los cambios controlados y la verificación contra la fuente externa no están implementados. La posición `paragraph_index` es ordinal del XML, no una página física; las páginas de un DOCX dependen de la maquetación. La API encola la conversión DOCX y el trabajador la ejecuta por separado.

`OPENALEX_CONTACT_EMAIL` es opcional. Un fallo de OpenAlex produce `SEARCH_UNAVAILABLE`; nunca se fabrican registros. `METADATA_CHECKED` significa que se consultó una ficha de OpenAlex por ID. `PENDING_EXTRACTION` significa que el PDF local espera al trabajador. `TEXT_CHECKED` significa que `pdfinfo` contó las páginas físicas y `pdftotext` extrajo texto localizado; **no** confirma título y autores contra la portada ni verifica las afirmaciones científicas. Estas dos comprobaciones se declaran `false` en la respuesta. Si falta el PDF externo, falla la descarga o no se puede extraer texto, la fuente externa permanece en metadatos; el resultado del trabajo indica qué ocurrió. No se generan extractos desde un resumen o desde metadatos.

En una carga del estudiante, `label` es solo el nombre asignado por la persona; la respuesta lo devuelve como `display_label`, con `title=null` y `title_verified_against_cover=false`. La petición comprueba cabecera PDF, tamaño y hash SHA-256; el trabajador comprueba después las páginas físicas y extrae el texto. Mientras tanto, la fuente permanece en `PENDING_EXTRACTION`. Si el archivo no tiene texto seleccionable, pasa a `OCR_REQUIRED` sin extractos. Solo el titular del proyecto puede cargarlo; los participantes autorizados pueden consultar la ficha y los extractos. El límite local de tamaño se define en `thesis/integrations/pdf.py`.

Si OpenAlex marca `is_retracted=true`, la fuente queda en `REJECTED`: se muestra el registro para revisión, pero no se descarga ni se ofrecen extractos. La bandera es un dato del catálogo, no una investigación independiente de retractaciones.

El OCR crea un PDF derivado y conserva el hash del original y de la copia. Solo marca `TEXT_CHECKED` cuando Poppler confirma que la copia tiene el mismo número de páginas físicas y extrae texto. El OCR no verifica que la transcripción sea correcta. GROBID puede extraer estructura y bibliografía, pero sus títulos, autores y DOI no sustituyen la verificación contra portada y registro oficial. Crossref coteja el registro DOI, no el contenido ni la portada; RapidFuzz propone coincidencias y `locate` devuelve siempre el texto físico recuperado, sin afirmar que sostiene una conclusión. pgvector ordena pasajes candidatos por similitud; esa puntuación tampoco acredita respaldo científico. La descarga y extracción de PDF, el OCR, GROBID, la indexación, Crossref y la conversión DOCX se ejecutan en el trabajador separado. La consulta inicial de metadatos a OpenAlex ocurre durante la petición. La comprobación humana de la portada y la validación de citas quedan pendientes. Los límites locales de descarga y páginas están en `thesis/integrations/pdf.py`; no son métricas de calidad documental.

La búsqueda de Semantic Scholar sigue la [API oficial Academic Graph](https://api.semanticscholar.org/api-docs/). `SEMANTIC_SCHOLAR_API_KEY` es opcional y, si está presente, se envía en `x-api-key`. Los resultados nunca pasan automáticamente a `SourceDocument` ni se presentan como texto inspeccionado.

## Verificación

```bash
DJANGO_DEBUG=1 .venv/bin/python backend/manage.py check
DJANGO_DEBUG=1 .venv/bin/python backend/manage.py makemigrations --check --dry-run
DJANGO_DEBUG=1 .venv/bin/pytest -q
```

Las pruebas usan PostgreSQL; el usuario de desarrollo debe poder crear la base temporal de pruebas. Cubren aislamiento entre proyectos, conflicto de versión, token MCP, CSRF, el recorrido MCP y la incorporación de fuentes con extractos localizados. La extracción se comprueba también con un PDF ya auditado en `docs/antecedentes_descargados/`.
