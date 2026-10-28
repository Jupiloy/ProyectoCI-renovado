# B4 — Citas estructuradas, IEEE, evidencia y Zotero

**Estado del código:** implementación B4.1–B4.5 presente en el repositorio.  
**Alcance funcional real:** citas estructuradas vinculadas al documento canónico, vista IEEE preliminar, revisión humana de evidencia y propuestas de sustitución con aceptación explícita, además de conexión OAuth de solo lectura con biblioteca personal Zotero.  
**Límites:** formato IEEE aún genérico/preliminar; no se ha hecho una conexión OAuth real porque faltan credenciales de una aplicación Zotero; no hay evaluación semántica automática ni campos Zotero vivos en DOCX exportado.

Esta guía describe el comportamiento físico comprobable en código. No convierte referencias importadas en referencias verificadas ni afirma que una cita respalde una afirmación por el mero hecho de estar registrada.

## 1. Para qué sirve B4

B4 reduce el trabajo repetitivo de registrar, ordenar, revisar y corregir citas dentro del documento de tesis:

1. El tesista coloca una o varias fuentes en una posición concreta del editor web y el backend conserva esa ocurrencia junto a una revisión inmutable del documento.
2. La plataforma numera referencias por primera aparición y presenta una bibliografía IEEE preliminar basada en metadatos congelados.
3. El tesista puede enlazar una afirmación citada con un pasaje localizable de la fuente. El sistema comprueba identidad, origen y localización como dimensiones separadas; el asesor decide si el pasaje respalda, contradice, no corresponde o resulta insuficiente.
4. Si se propone otra fuente, el sistema muestra la sustitución y su diferencia bibliográfica. Solo la aceptación explícita del titular crea una nueva revisión del documento; la revisión previa permanece intacta.
5. El usuario puede consultar e importar elementos bibliográficos desde su biblioteca Zotero personal. La conexión no replica Zotero, no descarga adjuntos y no escribe en la biblioteca.

La web propia sigue siendo el espacio principal de edición. Zotero es una biblioteca externa opcional que aporta metadatos. La detección de campos activos Zotero dentro de DOCX importados es una función distinta y no certifica que las citas creadas en TesisMCP mantengan campos editables en una exportación.

## 2. Modelo y persistencia

Migraciones B4: `0031`–`0035` (cinco migraciones aditivas; revisar nombres concretos en `backend/thesis/migrations/`). Conteo esperado del corte: 45 modelos Django y 35 migraciones. El verificador del repositorio es la comprobación final de estos conteos.

### `ChapterCitationOccurrence`

Una fila representa **una fuente dentro de una marca de cita**. Un grupo puede contener varias fuentes, cada una con su `source_order`. La ocurrencia se ancla a:

- `ChapterDocumentRevision` específica, nunca al texto mutable sin versión;
- `group_id` y `group_order` de la marca;
- `block_id` y `char_offset` del árbol canónico;
- `SourceDocument` del mismo proyecto;
- localizador opcional, por ejemplo página o sección;
- copia congelada de los metadatos de referencia y `reference_sha256`;
- usuario y fecha de creación.

El guard de PostgreSQL exige fuente del mismo proyecto y bloque/ancla válido, y hace append-only el historial. La restricción permite varias fuentes por grupo; el trigger mantiene consistente la relación entre `group_id` y `group_order`. No se borran/actualizan ocurrencias antiguas cuando el capítulo cambia: una revisión nueva recibe un manifest nuevo.

`ChapterDocumentRevision.citation_manifest_sha256` forma parte de la procedencia e idempotencia de la revisión. Los snapshots incorporan la huella y los datos congelados de cita al someter el capítulo. La exportación del snapshot aprobado usa ese manifest y no reconsulta metadatos actuales del catálogo.

### `CitationEvidenceReview`

Historial append-only para una afirmación, una cita y un pasaje de la fuente citada. Congela texto, offsets, página física, hashes y actor. Las decisiones humanas son `CANDIDATE`, `SUPPORTS`, `CONTRADICTS`, `UNRELATED` e `INSUFFICIENT`. Cada revisión nueva apunta a la anterior y usa número de versión e idempotencia. Un estado `CANDIDATE` no es una aprobación.

### Reemplazo de fuente

`CitationReplacementProposal` conserva revisión de origen, fuente anterior y alternativa, snapshots/hash de sus metadatos, motivo y versión esperada. `CitationReplacementDecision` registra una decisión única (`ACCEPTED` o `REJECTED`). La base protege historial y coherencia de proyecto/revisión. La aceptación crea una nueva revisión canónica y nuevas ocurrencias; la ocurrencia histórica conserva la fuente original.

### `ZoteroConnection`

Una conexión por usuario, con ID de usuario Zotero, scopes, fechas y API key cifrada en reposo. El secreto descifrado nunca se incluye en respuestas de estado. La clave Fernet configurada debe persistir y protegerse como secreto de servidor; rotarla sin migrar las credenciales haría imposible descifrar las claves ya guardadas.

## 3. Contrato del editor y numeración IEEE

`PUT /api/v1/projects/{project_id}/chapters/{chapter_no}/document` acepta el árbol canónico v1, la versión esperada, la clave idempotente y una lista `citations`. Cada marca contiene:

```json
{
  "group_id": "UUID",
  "block_id": "UUID de un bloque paragraph",
  "position": 12,
  "sources": [
    {"source_id": "UUID de SourceDocument", "locator": "p. 14"}
  ]
}
```

`position` es un offset de caracteres dentro del párrafo; cada fuente debe existir en el mismo proyecto. Se validan tipo de bloque, rango, duplicados, límites y versión. El servicio congela metadatos en cada ocurrencia. No admite colocar cita en encabezado ni en un bloque inexistente. Las marcas se vuelven a enviar con la revisión del árbol cuando se guarda una nueva versión; el cliente debe preservar los UUID de bloques estables.

`GET /api/v1/projects/{project_id}/chapters/{chapter_no}/citations/ieee` compone la vista vigente. El número se asigna por primera aparición según orden de bloque y offset; dentro de una marca con múltiples fuentes se mantiene `source_order`. Las apariciones posteriores reutilizan el número ya asignado. Al reordenar el manuscrito, los números pueden cambiar en la nueva revisión.

La salida está expresamente etiquetada como preliminar. Usa campos bibliográficos genéricos y señala metadatos faltantes; no implementa aún plantillas IEEE completas por tipo documental ni debe confundirse con una validación de conformidad editorial. En el DOCX de snapshot aprobado, los marcadores insertados y referencias proceden de los datos congelados. `GET /api/v1/projects/{project_id}/export/draft.docx` mantiene su contrato anterior.

La validación de aceptación debe incluir metadatos correctos para el tipo de documento, puntuación, abreviaturas, DOI/URL y fecha de acceso cuando aplique, capitalización, orden de autores, localizadores y correspondencia completa cita–referencia. B4 no afirma haber completado esa auditoría.

## 4. Identidad bibliográfica y respaldo de afirmaciones son verificaciones distintas

- `SourceMetadataCheck`/Crossref aporta una comprobación de metadatos del DOI, no que el texto cite correctamente ni que una fuente apoye una afirmación.
- `SourceDocument.verification_status=TEXT_CHECKED` indica procesamiento/localización textual según el flujo existente; no garantiza exactitud de OCR, identidad en portada o pertinencia científica.
- El endpoint de evidencia solo toma un `SourceExcerpt` de la misma fuente citada, en estado `TEXT_CHECKED`, y confirma rangos/hash/texto. Esto acredita que el fragmento está localizado en el texto almacenado.
- `automated_semantic_assessment` devuelve `NOT_PERFORMED`. No se afirma que un LLM haya inferido respaldo.
- El asesor agrega una evaluación humana con estado explícito. Solo esa acción produce `SUPPORTS`, `CONTRADICTS`, `UNRELATED` o `INSUFFICIENT`; la plataforma conserva quién, cuándo y qué versión decidió.

## 5. Propuestas de sustitución de citas

El titular o asesor puede proponer otra fuente del mismo proyecto, con justificación mínima, dentro de la revisión vigente. La propuesta queda pendiente y muestra una comparación (`from`, `to`) de referencias congeladas y una vista IEEE. Si cambió el documento o los metadatos propuestos ya no coinciden con su hash, la decisión se rechaza por conflicto y hay que generar una propuesta nueva.

Solo el titular puede aceptar o rechazar. La aceptación explícita cambia esa ocurrencia en una revisión nueva conservando texto, orden, grupos y localizadores; no reescribe el historial. El rechazo solo registra la decisión. El backend no elige fuente por similitud, conteo de citas, métricas de revista ni recomendación automática.

## 6. Integración Zotero: alcance y puesta en marcha

La integración implementada usa OAuth **1.0a** de Zotero, no OAuth 2.0. Es necesario registrar la aplicación/consumidor en Zotero y configurar callback y secretos en el entorno del servidor. Solicita acceso de lectura a biblioteca personal, sin notas, escritura ni grupos. La conexión produce una clave de API de larga duración, cifrada con Fernet en base de datos.

Variables requeridas:

| Variable | Uso |
|---|---|
| `ZOTERO_OAUTH_CLIENT_KEY` | Clave pública/identificador OAuth de la aplicación registrada. |
| `ZOTERO_OAUTH_CLIENT_SECRET` | Secreto OAuth de la aplicación; solo servidor. |
| `ZOTERO_OAUTH_CALLBACK_URL` | Callback registrado; HTTPS en despliegue y HTTP solo para localhost exacto durante desarrollo. |
| `ZOTERO_CREDENTIAL_ENCRYPTION_KEY` | Clave Fernet de servidor para cifrar las API keys de usuarios en reposo. |

No hay credenciales de desarrollo en el repositorio ni se ha ejecutado una ida/vuelta OAuth real. Sin las cuatro variables configuradas y la app registrada, el flujo falla cerrado con error de configuración. No pegar secretos en logs, prompts, frontend, commits o ejemplos versionados.

El listado consulta únicamente biblioteca personal por API v3, con paginación acotada. Importar un elemento crea `SourceDocument` con `record_provider=ZOTERO`, `metadata_origin=PROVIDER_API` y `verification_status=UNVERIFIED_METADATA`. No descarga adjuntos ni marca PDF como leído/verificado. Se deben cargar/inspeccionar los textos y validar portada/pertinencia por los flujos existentes.

Al desconectar, el servicio intenta revocar la clave remota y siempre borra el cifrado local. Si el proveedor falla o no confirma revocación, responde `MANUAL_REVOCATION_REQUIRED` y ruta de revocación del usuario. La API key es de larga duración según Zotero, así que el usuario debe revisar la revocación remota si el intento falla.

Documentación primaria de Zotero: [Web API v3](https://www.zotero.org/support/dev/web_api/v3/), [OAuth 1.0a](https://www.zotero.org/support/dev/web_api/v3/oauth), [operaciones de escritura/revocación](https://www.zotero.org/support/dev/web_api/v3/write_requests) y [conceptos básicos/uso de claves](https://www.zotero.org/support/dev/web_api/v3/basics).

## 7. Rutas HTTP B4

Todas las rutas de proyecto verifican usuario autenticado y pertenencia; los servicios limitan escritura a los roles señalados. Las rutas Zotero requieren sesión autenticada.

| Método y ruta | Uso / permiso / resultado |
|---|---|
| `PUT /api/v1/projects/{id}/chapters/{n}/document` | Guarda árbol y marcas estructuradas con `expected_version`/`idempotency_key`; titular. |
| `GET /api/v1/projects/{id}/chapters/{n}/citations/ieee` | Vista previa IEEE preliminar para participantes del proyecto. |
| `POST /api/v1/projects/{id}/chapters/{n}/citations/{occurrence_id}/evidence` | Crea vínculo candidato afirmación–pasaje exacto; titular. |
| `GET /api/v1/projects/{id}/chapters/{n}/citations/{occurrence_id}/evidence` | Historial de candidatos y revisiones de esa ocurrencia; miembro. |
| `POST /api/v1/projects/{id}/chapters/{n}/citation-evidence/{review_id}/decision` | Decisión humana versionada del asesor, con estado, versión e idempotencia. |
| `POST /api/v1/projects/{id}/chapters/{n}/citations/{occurrence_id}/replacement-proposals` | Propuesta de fuente alternativa con motivo; titular o asesor. |
| `GET /api/v1/projects/{id}/chapters/{n}/citation-replacement-proposals/{proposal_id}` | Comparación y vista preliminar; miembro. |
| `POST /api/v1/projects/{id}/chapters/{n}/citation-replacement-proposals/{proposal_id}/decision` | Acepta o rechaza con versión esperada; solo titular. Aceptación crea revisión nueva. |
| `GET /api/v1/integrations/zotero` | Estado no secreto de conexión del usuario. |
| `GET /api/v1/integrations/zotero/connect` | Inicia redirección OAuth y guarda solicitud temporal en sesión. |
| `GET /api/v1/integrations/zotero/callback` | Valida solicitud y sesión, intercambia token y cifra clave. |
| `DELETE /api/v1/integrations/zotero` | Intenta revocar clave remota y elimina clave local. |
| `GET /api/v1/projects/{id}/sources/zotero?query=&start=0&limit=25` | Busca/lista la biblioteca personal conectada, sin descargar adjuntos. |
| `POST /api/v1/projects/{id}/sources/import-zotero` | Cuerpo `{ "item_key": "XXXXXXXX" }`; titular importa un registro bibliográfico como metadatos no verificados. |

## 8. Dependencias, verificación y límites de demostración

Las dependencias Python añadidas al backend son `requests-oauthlib` y `cryptography`; revisar `requirements-backend.txt` para rangos vigentes. Las pruebas cubren servicios, permisos, cifrado local, validaciones y reglas PostgreSQL del dominio. Un test con OAuth/HTTP simulado demuestra el contrato local, no acceso real a Zotero. Antes de una demostración real, configurar una app de prueba, callback HTTPS accesible, clave Fernet protegida y una cuenta Zotero de prueba; confirmar lectura, importación, desconexión y revocación en la cuenta.

### Preparación de una prueba local Zotero

1. Crear/registrar una aplicación OAuth de prueba en Zotero y configurar el callback exactamente como el entorno local, por ejemplo `http://127.0.0.1:8000/api/v1/integrations/zotero/callback`. Para nube, el callback debe ser HTTPS y coincidir exactamente con el registrado.
2. Guardar key/secret en `.env` local (`ZOTERO_OAUTH_CLIENT_KEY`, `ZOTERO_OAUTH_CLIENT_SECRET`, `ZOTERO_OAUTH_CALLBACK_URL`), nunca en Git ni en el frontend. Crear una `ZOTERO_CREDENTIAL_ENCRYPTION_KEY` Fernet y conservarla respaldada: cambiarla sin migrar las credenciales cifradas impide descifrarlas.
3. Iniciar el backend con Compose; verificar que el servicio `web` recibe las cuatro variables. Iniciar sesión con cookie Django y CSRF y abrir `GET /api/v1/integrations/zotero/connect`. La callback OAuth completa el enlace de esa misma sesión.
4. Consultar estado, listar la biblioteca, importar un ítem de prueba, comprobar `UNVERIFIED_METADATA` y desconectar. Si la revocación remota falla, usar el enlace de revocación manual devuelto por el servicio.

La configuración local queda preparada en [.env.example](../../.env.example); contiene valores vacíos, no credenciales reales. La preparación no prueba OAuth hasta ejecutar el recorrido con una cuenta real.

B4 no implementa: campos CSL de Zotero vivos en los DOCX de TesisMCP; escritura/sincronización hacia Zotero; descarga de adjuntos desde biblioteca; estilos IEEE completos específicos por tipo documental; verificación automática de que fuente apoya afirmación; llamadas LLM para evaluar citas; frontend visual de estas rutas; ni OAuth externo probado con credenciales de producción.

No confundir `ManuscriptCitation` con `ChapterCitationOccurrence`: el primer modelo registra campos detectados al importar DOCX; el segundo es una cita estructurada del documento canónico web. P20 admite IEEE y conserva APA 7 por compatibilidad; la vista B4 usa citas estructuradas propias del editor. La actualización no reescribe recorridos publicados ni certifica formato IEEE.
