# Paso 2 — Documento canónico y editor web

Fecha de inspección del código: 27/10/2026. Checkout de trabajo: `ProyectoCI-renovado`. Frontend a integrar: `TesisMCP/`. Esta numeración describe la **integración de frontend**: no es el bloque backend B2 ni uno de los prompts P01–P32.

## Estado y decisión de alcance

El paso 1 conectó sesión y selección de proyectos. La comprobación en navegador con Django y una cuenta real sigue pendiente; el contrato y la compilación focalizada de 1B constan en [el documento del paso 1](paso_1_acceso_y_seleccion_proyecto.md).

**Estado:** 2A (contrato) y 2B (editor acotado) realizados. En 2C se comprobó por HTTP real la ida y vuelta Vite → Django → PostgreSQL aislado y se corrigió el reintento idempotente del backend. La inspección visual y las interacciones del componente en navegador siguen pendientes porque el navegador local está deshabilitado en Work. La puerta global se reserva para el cierre de las correcciones acordadas.

La decisión para 2B es un editor **por bloques del árbol canónico**, dentro de la interfaz propia. Los seis bloques textuales existentes serán editables con campos controlados; tablas y figuras v2 existentes se conservarán como nodos estructurados y se mostrarán como elementos de solo lectura en esta entrega. Las marcas bibliográficas ya existentes deben preservarse en cada guardado. La demo visual permanece separada en `TesisMCP/src/DemoApp.tsx`; no se traslada su contenido ficticio a un proyecto real.

## Fuentes de verdad inspeccionadas

La revisión confirmó una diferencia que debe conservarse en los tipos: GET de documento canónico presenta `citations`, `citation_manifest_sha256` y `source`; la proyección legada no los incluye. No se debe normalizar esa diferencia inventando metadatos para revisiones antiguas. La ruta de guardado valida marcas contra el árbol y las fuentes del proyecto, y la persistencia incrementa tanto `document_version` como `state_version`.

- Rutas: `backend/thesis/api/routes_chapters.py` y `backend/thesis/api/schemas.py`.
- Árbol, proyección y persistencia: `backend/thesis/services/chapter_documents.py`.
- Marcas de cita: `backend/thesis/services/citation_occurrences.py`.
- Estado de capítulo: `backend/thesis/services/chapter_queries.py` y `backend/thesis/models/chapters.py`.
- Referencias de tablas y figuras: `backend/thesis/services/document_artifacts.py`.
- Contexto previo: [documento canónico](paquete_b1_b2_2_documento_canonico.md), [propuestas IA](paquete_b1_b2_3_diffs_ia_documento.md), [datos y figuras](paquete_b8_datos_figuras.md), [matriz de integración](matriz_integracion_frontend_backend.md).

Cuando un paquete histórico describa solo schema v1, prevalece `chapter_documents.py`: hoy acepta v1 y v2. El ADR-BE-06 continúa propuesto hasta observar una ida y vuelta real sin pérdida con el editor frontend.

## Rutas necesarias para 2B

Base `/api/v1`; sesión Django con cookies y CSRF de 1B. Todos los IDs del proyecto provienen de la selección autorizada.

| Método | Ruta | Uso y restricciones |
| --- | --- | --- |
| `GET` | `/projects/{project_id}/chapters/{chapter_no}` | Estado del capítulo y referencias a snapshots; sirve para permitir o bloquear edición. Responde `status`, `chapter_no`, `latest_revision`, `approved_snapshot_id`, `submitted_snapshot_id` y `steps`. |
| `GET` | `/projects/{project_id}/chapters/{chapter_no}/document` | Lectura autorizada del documento o proyección legada de solo lectura. No persiste por consultar. |
| `PUT` | `/projects/{project_id}/chapters/{chapter_no}/document` | Guarda una revisión canónica. Solo titular activo. Cuerpo JSON exacto para esta ruta: `content_tree`, `citations`, `expected_version`, `idempotency_key`. `X-CSRFToken` en cabecera. |

`CHAPTER_STEPS` se deriva del catálogo físico y determina qué números de capítulo tienen ruta. **No fijar un capítulo, título o cantidad de pasos desde la maqueta.** Para 2B se puede ofrecer un selector de capítulos disponibles, pero su contenido visual no debe inferirse de los 32 prompts; la estructura metodológica configurable se conectará después. Si un capítulo no existe todavía como fila, el GET devuelve estado `DRAFT` y un documento/proyección vacía.

## Contrato de lectura

El GET canónico puede incluir:

```ts
{
  chapter_no: number,
  document_version: number,
  revision_id: string | null,
  revision_no: number | null,
  schema_version: 1 | 2,
  content_tree: { schema_version: 1 | 2, blocks: Block[] },
  content_md: string,
  content_sha256: string,
  state_version: number | null,
  is_legacy_projection: boolean,
  is_stale: boolean,
  citations?: CitationMarkRead[],
  citation_manifest_sha256?: string,
  source?: string
}
```

La forma exacta depende de la rama del servicio: la lectura de una **proyección legada** incluye `content_tree`, `content_md`, versión y banderas, pero hoy no añade `citations`, `citation_manifest_sha256` ni `source`. El frontend debe interpretar `citations` ausente como ausencia de marcas estructuradas en esa proyección, sin atribuirles citas verificadas.

`document_version` es la versión optimista del documento; `state_version` corresponde al perfil global. Para el PUT se envía `expected_version = document_version`, **no** `state_version`. `is_stale=true` indica que el estado metodológico cambió desde la última revisión documental; mostrar la advertencia y exigir una decisión explícita de recarga/reconciliación antes de enviar el capítulo. Un guardado de la misma estructura tras revisar el contexto puede actualizar la versión, pero crea una revisión nueva.

Un `revision_id=null` con `is_legacy_projection=true` indica texto derivado de revisiones por pasos, no un documento editado previamente. El usuario debe reconocer que el primer PUT materializa una nueva versión; no escribir en el GET ni presentar esa proyección como edición ya persistida.

## Árbol v2 que el editor debe conservar

La raíz tiene **exactamente** `schema_version` y `blocks`. Cada bloque tiene un UUID canónico único. Para el PUT de una versión cargada v1, conservar v1 mientras no sea necesaria la estructura v2; si se decide elevar a v2, hacerlo de forma explícita y sin alterar IDs o contenidos. Un documento nuevo puede usar v2. No inventar campos de estilo en el JSON.

| Tipo | Campos exactos además de `type` e `id` | Edición 2B |
| --- | --- | --- |
| `heading` | `level` entero 1–6, `text` | Texto y nivel. |
| `paragraph` | `text` | Texto plano. |
| `blockquote` | `text` | Texto plano. |
| `code_block` | `text` | Texto plano, admite vacío. |
| `bullet_list` | `items` lista de textos | Editar ítems; nunca guardar lista vacía. |
| `ordered_list` | `items` lista de textos | Editar ítems; nunca guardar lista vacía. |
| `data_table` (v2) | `table_version_id`, `result_sha256`, `caption` | Conservar ID, hash y caption; mostrar placeholder estructurado. |
| `figure` (v2) | `figure_version_id`, `output_sha256`, `caption` | Conservar ID, hash y caption; mostrar placeholder estructurado. |

Límites verificados en `normalize_content_tree`: hasta 1 000 bloques; hasta 20 000 caracteres por bloque textual o ítem; listas de 1 a 500 ítems; 200 000 caracteres de texto total y también de Markdown proyectado. En v1 no se admiten `data_table`/`figure`. Referencias v2 requieren UUID canónico, hash SHA-256 hexadecimal minúsculo de 64 caracteres y caption no vacío hasta 500 caracteres; el backend valida pertenencia e integridad del artefacto antes de guardar.

**No convertir una tabla o figura a Markdown o texto plano** durante el guardado. El Markdown es una proyección de compatibilidad y no permite reconstruir todos los nodos. Mostrar los nodos de artefacto sin borrarlos, incluso si 2B todavía no ofrece crear nuevas tablas o figuras. Si el editor no reconoce un nodo devuelto por una futura versión de esquema, abrirlo en solo lectura y bloquear el PUT hasta contar con soporte, para evitar pérdida.

## Marcas de cita: datos aparte del texto

En el cuerpo del PUT, cada grupo requiere exactamente:

```json
{
  "group_id": "UUID",
  "block_id": "UUID de un paragraph existente",
  "position": 0,
  "sources": [{ "source_id": "UUID", "locator": "" }]
}
```

`position` es un offset **Unicode en puntos de código Python** dentro del texto del párrafo; rango inclusivo `0..len(text)`. La marca solo puede apuntar a `paragraph`; cada grupo y fuente dentro del grupo son únicos. Cada grupo lleva de 1 a 20 fuentes; el documento admite hasta 500 grupos y 1 000 ocurrencias. El backend comprueba que cada fuente exista en el proyecto. No se deben tomar offsets JavaScript UTF-16 sin conversión: emoji y otros caracteres suplementarios crean desplazamientos distintos.

El GET de una revisión canónica añade `sources[].source_order`, `sources[].reference` y `sources[].reference_sha256` para lectura. **El PUT no acepta esos campos adicionales**: mapear cada marca al formato de entrada y conservar `group_id`, `block_id`, `position`, `source_id` y `locator` para marcas que sigan válidas. No asumir que `citations=[]` es un mero valor por defecto seguro: enviarlo borra las marcas de la revisión nueva. Si se edita/elimina un párrafo con citas o se mueve su contenido, la UI debe ajustar el offset por un algoritmo comprobado o pedir decisión explícita sobre cada marca; mientras no exista ese algoritmo, bloquear el guardado de una modificación que invalide posiciones o identidad del bloque. El soporte de inserción de nuevas citas con búsqueda de fuentes corresponde a una ampliación posterior, pero conservar marcas existentes es requisito de 2B.

## Estado, permisos y guardado

- `OWNER` puede pedir el PUT si el capítulo está `DRAFT` o `CHANGES_REQUESTED`; `ADVISOR` puede consultar y debe ver controles de edición deshabilitados. El backend revalida cada operación.
- `READY` y `APPROVED` son solo lectura para este editor. `CHANGES_REQUESTED` vuelve a edición cuando el titular guarda y el backend hace la transición.
- El usuario edita un **borrador local separado** de la respuesta GET. Cambiar de capítulo, proyecto, cerrar sesión o salir de pantalla con cambios pendientes debe mostrar decisión de conservar localmente en memoria/volver o descartar; no afirmar que se guardó.
- El botón Guardar construye un snapshot del borrador, genera `idempotency_key` UUID para **ese contenido y esas citas**, manda `expected_version=document_version` y deshabilita doble envío. Si se pierde la respuesta, un reintento del **mismo payload** conserva la misma clave; si el contenido cambia, genera otra clave. Nunca enviar la clave en lugar del campo JSON.
- La respuesta del PUT trae nueva `document_version`, `revision_id`, `content_tree`, `citations`, `state_version`, `is_stale` e `idempotent`. Actualizar el estado local solo con la respuesta confirmada y comparar con el borrador enviado para no borrar ediciones hechas mientras la petición estaba en vuelo.
- 409 `VERSION_CONFLICT`: mantener el borrador local, consultar versión actual por GET, ofrecer comparación/reconciliación explícita. No sobrescribir, fusionar ni repetir PUT automáticamente. 409 `IDEMPOTENCY_CONFLICT` requiere nueva revisión de clave/payload, sin reenvío ciego.
- 400/422 de validación: mostrar el detalle útil y conservar borrador. 401: limpiar contexto y volver a acceso según el flujo de 1B. 403: distinguir CSRF conocido de `PERMISSION_DENIED`; después de refrescar CSRF el usuario decide si reenvía. 404 de proyecto/capítulo: ocultar datos ajenos y volver a selección o mostrar capítulo no disponible. 409 de capítulo en revisión/aprobado: recargar estado y bloquear edición.
- `apiRequest` actual parsea JSON; las descargas DOCX/PNG requieren otro cliente o un método binario posterior. No añadirlas a esta tarea por accidente.

## Diseño de 2B: editor real acotado

1. Añadir funciones API `getChapterState`, `getChapterDocument`, `saveChapterDocument` y tipos estrechos. No poner `fetch` dentro de componentes. La sesión/CSRF y `selectedProject` salen de `App.tsx`, no de un ID en URL sin autorizar.
2. Crear `features/editor/` con contenedor de carga, panel de navegación de capítulos, barra de estado, lista de bloques y controles de guardado. Basar la composición visual en `DemoApp.tsx` y `index.css`, manteniendo sus datos de ejemplo dentro de la demo.
3. Abrir primero un capítulo elegido por el usuario y traer **en paralelo** estado de capítulo y documento. Distinguir carga, ausencia de texto, proyección legada, revisión guardada, versión obsoleta y error de lectura. No mostrar avance, citas ni títulos de capítulo inventados.
4. Representar cada bloque textual por un editor controlado (texto y nivel/ítems según tipo). Añadir bloque con `crypto.randomUUID()` y conservar IDs de bloques existentes al editar o reordenar. La hoja completa `contentEditable` del demo no se usa como fuente de verdad.
5. Mostrar controles solo para operaciones respaldadas por el esquema. Negrita, cursiva, estilos arbitrarios, arrastre de citas y edición WYSIWYG de tablas/figuras se dejan deshabilitados o con explicación de disponibilidad; no fingir que el backend los guarda.
6. Montar el payload de PUT desde una copia íntegra del árbol y marcas. El formulario puede bloquear la edición de bloques con citas hasta resolver la reubicación de offsets. Los artefactos v2 se preservan exactamente. No usar `content_md` como payload canónico.
7. Confirmar guardado y versión solo después del PUT. Mostrar conflicto o incertidumbre de red sin afirmar «guardado». En una respuesta incierta, mantener clave y payload del intento para consulta/reintento idempotente; consultar GET antes si hay duda sobre el estado resultante.
8. Cambiar de capítulo/proyecto o cerrar sesión con borrador sucio requiere una decisión visible. El guardado pertenece al titular; el asesor solo consulta. No conectar aún envío/decisión de asesor, diff IA, comentarios, IEEE ni exportación.
9. Actualizar esta guía y la matriz con los archivos concretos, estado de la compilación y límites observados. Las comprobaciones focalizadas de tipos/build son suficientes para este incremento mientras el usuario reserva la puerta global para el cierre; una prueba real en navegador sería evidencia distinta.

## Criterios de aceptación de 2B/2C

- El mismo árbol y las mismas marcas de cita pueden leerse, guardarse sin cambios y releerse sin pérdida de IDs, tipo, orden, texto, referencias de artefactos y anclas. Se inspecciona por separado una revisión v1, un árbol v2 con tabla/figura y una proyección legada. Si no hay datos reales para alguno, no anunciarlo como verificado.
- Un `ADVISOR`, un capítulo `READY`/`APPROVED`, una sesión vencida y una membresía revocada no producen un editor escribible ni un PUT aceptado.
- Un `VERSION_CONFLICT`, una respuesta de red perdida y un error de validación conservan el borrador y no producen duplicaciones ni texto «guardado» falso.
- Un texto con caracteres suplementarios no desplaza ni rompe citas al editar; hasta que eso pueda probarse, la UI bloquea las operaciones que afecten anclas existentes.
- La demo se mantiene como vista explícita y no aporta datos al proyecto real.
- `pnpm exec tsc --noEmit` y `pnpm build` con salida 0 después de la implementación. La puerta integral `python3 scripts/verify_project.py` permanece pendiente hasta el cierre global acordado; no afirmar que 2B está verificado por el mero hecho de compilar.

## Siguiente modelo

Para implementar el componente visual acotado con este contrato cerrado: **Luna, razonamiento Medium**. Para revisar pérdidas de información, citas Unicode, idempotencia y conflictos después de 2B: **Sol High**. Sol 5.6 también es apto si el usuario lo prefiere; la cuota Plus consumida por modelo/tarea no está garantizada por este documento.

## Registro de implementación 2B (2026-10-27)

Implementado en `TesisMCP/`:

- `src/api/types.ts` incorpora tipos estrechos para estado, árbol, bloques, citas y documento de capítulo.
- `src/api/chapters.ts` centraliza GET de estado/documento y PUT de guardado con la sesión/CSRF y el `apiRequest` compartido.
- `src/features/editor/ChapterEditorScreen.tsx` carga estado y documento en paralelo; presenta estado, versión, proyección legada y obsolescencia; permite elegir capítulos 1–7 (el conjunto comprobado hoy por `CHAPTER_STEPS`); edita bloques compatibles, reordena y conserva IDs; bloquea el texto y borrado de párrafos citados; conserva tabla/figura v2 sin editarlas; guarda con versión esperada e idempotencia; retiene el borrador si falla y requiere confirmación para descartarlo.
- `src/App.tsx` conecta la pantalla con el proyecto autenticado y la vista existente.
- `src/features/projects/ConnectedProjectScreen.tsx` expone el acceso al editor sin reemplazar la demo.
- `src/index.css` agrega estilos del editor y adaptación móvil.

**Comprobación realizada:** `pnpm exec tsc --noEmit` terminó con código 0; `pnpm build` terminó con código 0. El primer intento del build quedó bloqueado por escritura de Vite en `node_modules/.vite-temp` bajo el sandbox; el mismo comando autorizado en el directorio de trabajo terminó correctamente. No se ejecutaron pruebas ni la puerta global. No se inspeccionó el flujo en navegador con una sesión autenticada, ni se demostró lectura/guardado contra la base activa; por tanto 2C sigue pendiente y no se afirma que citas/artifacts v1/v2 hayan pasado una ida y vuelta real.

**Límites conocidos de 2B:** el selector reproduce el conjunto actual de capítulos 1–7 derivado del catálogo backend y deberá revisarse si ese catálogo cambia; la pantalla no ofrece inserción de citas, edición WYSIWYG, modificación de tablas/figuras, envío a revisión, comentarios ni aprobación. Las marcas se vuelven a enviar en la forma exacta aceptada por el PUT. El modo asesor es de consulta. Errores de red conservan payload y clave de idempotencia para reintentar; ante conflicto el usuario puede recargar explícitamente y descartar el borrador.

**Siguiente:** cambia a **Sol High** para auditar el contrato de citas, retención de borrador, permisos, estados y pérdida de datos antes de iniciar 2C. La auditoría debe distinguir lo demostrado por TypeScript/build de lo que requiere sesión real y datos backend.

## Revisión adversaria de 2B y preparación de 2C (27/10/2026)

La revisión con Sol High contrastó `ChapterEditorScreen.tsx` y `editorDocument.ts` con `chapter_documents.py`, `citation_occurrences.py`, el esquema de entrada de la API y el control de acceso por membresía. Se corrigió lo siguiente:

- **Materialización y obsolescencia:** el titular puede guardar una proyección legada o un documento nuevo sin modificar texto, y puede crear una revisión de un documento `is_stale` tras revisarlo. Después de guardar, el frontend consulta otra vez estado y documento; así refleja el cambio `CHANGES_REQUESTED → DRAFT` y la revisión realmente vigente.
- **Reintento idempotente y concurrencia:** un reintento puede devolver una revisión histórica mientras otro guardado ya es el vigente. La UI compara el `revision_id` devuelto con el GET actual y conserva el borrador si difieren. Los 409 y la pérdida de permiso bloquean un PUT adicional hasta consultar o recargar. «Consultar versión vigente» compara árbol y marcas; si coinciden, adopta el documento actual; si difieren, muestra ambas versiones como texto orientativo y pide decisión explícita para descartar. El botón no mezcla automáticamente árboles.
- **Protección de datos:** el frontend rechaza la edición si llega un esquema/bloque desconocido o si una revisión canónica omite citas. Los offsets existentes se comprueban como puntos de código Unicode. `beforeunload` avisa de borrador o intento pendiente; cambio de capítulo, vuelta al proyecto y cierre de sesión piden confirmación. Una solicitud antigua de carga no reemplaza un capítulo nuevo tras cambiar la selección. Los artefactos v2 se conservan y su eliminación permanece deshabilitada.
- **Operaciones textuales:** el editor permite crear los seis tipos textuales soportados por el árbol, además de editar los existentes; todos los bloques nuevos reciben UUID. El asesor y los estados `READY`/`APPROVED` siguen en consulta.
- **Documentación de estado:** se actualizan esta guía, la matriz, `GUIA_AGENTE.md`, `README.md` y `estado_version_producto.md` para distinguir el frontend parcial del corte backend previamente verificado.

**Evidencia focalizada final:** `pnpm exec tsc --noEmit` terminó con código 0 y `pnpm build` terminó con código 0 (26 módulos transformados). No se ejecutó `python3 scripts/verify_project.py` por el aplazamiento acordado de la puerta integral. Tampoco se afirma una ida y vuelta real: `podman ps` mostró solo `tesismcp-local-pg`; Django y Vite no estaban levantados. La base local `tesismcp` puede ser la misma que usa la carpeta original, según `GUIA_AGENTE.md`, por lo que 2C exige una base PostgreSQL y media aisladas antes de crear cuenta/proyecto de prueba o hacer escrituras.

**Hallazgo backend del corte de auditoría:** la respuesta a un reintento histórico mezclaba `document_version` actual con contenido anterior y el manifest recalculado podía fallar cuando cambiaban metadatos de una fuente. Ambos puntos se corrigieron en el siguiente corte 2C. La revisión visual en navegador sigue siendo necesaria para comprobar controles, alertas y conservación del borrador desde la interfaz.

**Próximo paso:** 2C con **Sol High** para preparar el entorno aislado y observar el recorrido autenticado en navegador. Si se usa Luna para ajustes puramente visuales, volver a Sol High para revisar integridad documental y permisos antes del cierre.

## Corte 2C: contrato HTTP real y corrección de idempotencia (27/10/2026)

Se creó la base independiente `tesismcp_frontend_2c` dentro del PostgreSQL local y se montó `/tmp/tesismcp_2c_media` como media separada. Django se ejecutó desde el código de esta copia en un contenedor local; Vite sirvió `TesisMCP/` en el puerto 8443 y reenvió `/api` a Django en el 8000. No se migró ni escribió en la base `tesismcp` de la carpeta original. Los usuarios, fuente, datos de tabla y figura usados fueron sintéticos y quedaron solo en la base aislada. La creación de base, migraciones `0001`–`0044` y la preparación de cuentas terminaron con código 0.

**Comprobaciones observadas por HTTP a través de Vite (código 0):** sesión/cookie/CSRF, login y logout, creación/listado de proyecto, carga de capítulo vacío, PUT y GET posterior del mismo árbol, reintento de clave, rechazo 409 de versión antigua, lectura del asesor y rechazo 404 de su escritura. Se materializó sin cambios una proyección legada de P06 en capítulo 2; un párrafo con emoji conservó su ancla de cita medida en puntos de código; un reintento histórico devolvió revisión 2 con `current_document_version=3` e `is_current=false`, mientras GET siguió mostrando la revisión 3. Un árbol v2 con tabla y figura reales sintéticas conservó ID de bloque, ID de artefacto, hash, caption y orden tras añadir otro bloque y guardar. `READY` rechazó PUT con 409; `CHANGES_REQUESTED` volvió a `DRAFT` tras PUT; tras revocar la membresía del asesor, el proyecto desapareció de su listado y GET del documento respondió 404. Los scripts de comprobación están en `/tmp/tesismcp_2c_*` y no forman parte del repositorio.

**Corrección backend:** `backend/thesis/services/chapter_documents.py` compara en un reintento las anclas y fuentes solicitadas con la revisión persistida, sin exigir que los metadatos bibliográficos actuales produzcan el mismo hash congelado. La respuesta histórica ahora usa `document_version` de esa revisión y añade `current_document_version` e `is_current`. Un cambio real de posición/cita con la misma clave sigue dando `IDEMPOTENCY_CONFLICT`. Se actualizó el caso focalizado en `backend/thesis/tests/test_citation_occurrences.py` y terminó **1 passed, exit 0**. El frontend continúa haciendo GET tras PUT para confirmar la versión vigente.

**Límite observable:** `cua_repl` devolvió “Local browser use is disabled in Work settings” y el inventario de navegadores estaba vacío. Por ello estas comprobaciones prueban el transporte y contrato HTTP, pero **no** la visualización ni los clics del editor. La validación manual/visual pendiente debe usar la misma base aislada y revisar guardado sin cambios, citas bloqueadas, artefactos de solo lectura, conflicto con borrador conservado y el cambio de estado visible. No se ejecutó `python3 scripts/verify_project.py`, conforme al aplazamiento del usuario.
