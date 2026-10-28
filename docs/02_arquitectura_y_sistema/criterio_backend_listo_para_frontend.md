# Criterio de backend listo para desarrollar el frontend

**Estado:** objetivo de entrega; no describe funcionalidades ya implementadas. **Fecha:** 25/10/2026. Este documento define qué significa «terminar el backend» para el producto acordado. El [estado verificado](../07_desarrollo_prototipo/estado_version_producto.md) conserva los hechos del corte de código; este archivo no los altera.

## 1. Decisión de alcance

Se construirá primero un backend **funcional de extremo a extremo**, consumible por la futura web propia y por MCP mediante servicios compartidos. «Listo para frontend» no significa que cada conector externo opcional tenga licencia ni que exista una interfaz gráfica terminada. Sí significa que las operaciones centrales, sus contratos HTTP, permisos, versiones, errores, trabajos en segundo plano, datos de ejemplo auténticos o claramente sintéticos, pruebas y documentación permiten implementar la interfaz sin inventar reglas de negocio en el navegador.

El backend tiene P01–P32 en modo legado secuencial y B5 implementa además un grafo configurable con tareas `USR_...`. B5.1 ya incorpora rutas, ciclo persistente de jobs, validación local estricta, aceptación humana, worker y adaptador Gemini; el proveedor está deshabilitado por defecto y una llamada real sigue pendiente de credenciales. El endpoint `POST .../workflow/tasks/{task_id}/execute` recibe `output_data` que ya produjo el cliente y lo persiste para tareas personalizadas. El destino incluye exploración abierta, búsqueda y corpus documental, citas IEEE trazables, revisión del asesor, preparación y análisis sobre **datos reales**, tablas/figuras derivadas de esos datos y exportación de una revisión congelada. Las rutas cuantitativa, cualitativa y mixta deben tener contratos diferenciados cuando sus tareas se habiliten; no se afirma que los prompts actuales cubran correctamente las tres.

El acuerdo académico con el profesor y la normativa UTP pueden cambiar una plantilla/versionado, pero no deben exigir reconstruir servicios, permisos o historial. Cada regla institucional requiere fuente, versión y ámbito; IEEE es la configuración del piloto acordado, no una norma UTP universal.

## 2. Recorridos completos que deben pasar antes del frontend

| Recorrido | Resultado observable desde API/cliente de prueba | Evidencia mínima de aceptación |
|---|---|---|
| Proyecto y método | Tesista crea proyecto, registra alternativas sin límite artificial, elige tema provisional, adapta y publica recorrido/prompts, consulta dependencias y cambios de versión. | Un segundo usuario no lee ni cambia el proyecto; dos ediciones concurrentes no se pisan; proyectos legados siguen legibles. |
| Literatura y fuentes | Diseña/guarda búsquedas web y ecuaciones para Scopus/WoS, abre la fuente oficial para búsqueda manual, importa un archivo exportado, deduplica, carga PDF/otros formatos validados y consulta pasajes con localizador. | Se distingue «metadatos», «resumen» y «texto extraído»; no se atribuye búsqueda manual al servidor ni lectura completa a metadatos. |
| Antecedentes y escritura | Trabaja estudios independientes en paralelo, crea fichas con evidencia; IA sugiere borradores, revisa coherencia y el tesista acepta o rechaza; citas del texto se enlazan a referencias y pasajes cuando existen. | Una cita falsa o pasaje inexistente no se marca verificado; se conserva la versión de fuente, prompt y contexto usada. |
| Asesoría | Asesor ve una instantánea íntegra, comenta fragmentos, solicita cambios, resuelve observaciones y aprueba la misma versión que será exportada. Una persona puede cubrir asesoría temática y metodológica. | Aprobación bloqueada por observaciones abiertas según política; cambios posteriores no alteran la revisión aprobada. |
| Preparación de campo | Registra diseño, participantes/muestra cuando aplique, instrumento, plan de análisis, permisos, consentimiento y estado de dictamen ético. La plataforma orienta y registra documentos, no emite autorizaciones UTP. | La actividad que exige dictamen no pasa a estado de ejecución autorizada sin registro válido; un coeficiente piloto requiere datos/procedimiento, no un número escrito por IA. |
| Datos y análisis | Ingiere datos originales con procedencia, permisos y versión; limpieza/transformaciones reproducibles; análisis apropiado al enfoque. En cualitativo, fragmentos/códigos/interpretaciones enlazados; en mixto, integración explícita. | Resultado reconstruible desde datos originales y transformaciones; sin datos reales el manuscrito de resultados queda pendiente. |
| Documento y entrega | Monta texto, citas IEEE, tablas/figuras recalculables y procedencia; exporta DOCX/PDF desde una instantánea aprobada e informa lo que realmente verificó. | Cita y referencia corresponden, gráficos reflejan datos versionados, exportación no cambia tras editar el proyecto. |

No basta con endpoints aislados: al menos un recorrido integrado debe unir proyecto → método → fuentes → borrador → revisión → datos auténticos de prueba → hallazgos → exportación. Para demostrar las ramas metodológicas, agregar recorridos focalizados de cuantitativo, cualitativo y mixto que prueben sus diferencias, sin imponer hipótesis, Likert, PRISMA o coeficientes a todas.

## 3. Capacidades transversales obligatorias

1. **API web estable:** OpenAPI con esquemas estrictos de entrada/salida, errores por código, paginación y filtros documentados. Contratos suficientes para que el frontend construya editor, biblioteca, panel de revisión, tareas y descargas. Ninguna ruta depende de un `user_id` suministrado por IA.
2. **Identidad, permisos y concurrencia:** tesista/asesor y apoyos invitados solo cuando se habiliten; autenticación del servidor, aislamiento de proyectos, `expected_version`/bloqueos, idempotencia y auditoría. Las invitaciones comparten únicamente tareas y recursos concedidos.
3. **Estado canónico y versiones:** recorrido, prompt, fuente, documento, revisión, dataset, figura, job y exportación están vinculados a versiones inmutables o reconstruibles. Cambios metodológicos muestran impacto, no reescriben aprobaciones.
4. **IA y agentes:** tareas tipadas con contexto fijado, costos/errores y posibilidad de cancelación; paralelismo para trabajos independientes; resultados como propuestas que requieren aceptación. La lógica de seguridad/academia reside en Django, no en el texto del prompt ni en n8n.
5. **Datos y evidencia:** conservar originales, hashes, localizadores y transformaciones. OCR y extracción no equivalen a lectura crítica; una comparación afirmación–cita muestra pasaje, acceso y motivo de su estado preliminar.
6. **Operación:** API y trabajador con PostgreSQL/almacenamiento privado, migraciones reproducibles, secretos fuera del código, respaldos restaurables, logs sin datos sensibles y prueba de recuperación. La configuración local por Podman debe documentarse según el repositorio real.

## 4. Integraciones: necesarias, opcionales y comprobables

- **Web abierta y archivos aportados/importados:** necesarios para el recorrido de búsqueda y corpus.
- **Scopus/WoS:** necesario el modo asistido sin API (ecuación, filtros, enlace oficial, registro e importación). APIs licenciadas son opcionales; no condicionan el cierre del núcleo.
- **Zotero:** integración bibliográfica deseada para el backend completo. Implementar autorización y biblioteca solo con scopes/acceso comprobados; si no están disponibles, mantener importación/exportación bibliográfica y declarar la conexión bloqueada, sin simular sincronización. Campos activos en DOCX son una característica distinta que requiere prueba externa.
- **LaTeX/BibTeX, n8n, conectores licenciados y otros servicios:** extensiones opcionales. Ninguna sustituye el modelo de documento, permisos o evidencia. Solo declarar implementadas las rutas probadas.
- **Proveedor LLM:** el backend debe tener adaptador de proveedor configurable, ejecución y aceptación observables. Si no hay credenciales, la lógica determinista puede probarse aislada, pero el recorrido IA real queda pendiente y debe constar así.

## 5. Secuencia de implementación hasta «listo para frontend»

La [tabla B0–B10](./plan_entregas_backend.md) conserva los nombres de entrega. Se permite combinar entregas verticales cuando una dependencia real lo exige. Orden recomendado de integración:

1. **Cerrar B5.1:** configurar credenciales de servidor y comprobar una ejecución real del adaptador Gemini, separada de la suite simulada; mantener el mock solo para desarrollo/pruebas y evaluar privacidad, costo y límites antes de producción. Las rutas/job/contexto/aceptación ya existen; el `execute` sigue siendo una operación distinta que persiste salida recibida desde el cliente.
2. **B1 + B2:** instantánea completa de capítulo, aceptación de una propuesta como revisión canónica, aprobación/exportación coherente y API web base. El futuro editor consume este contrato; no esperar a construir la interfaz para fijar el modelo canónico.
3. **B3 + B7:** búsqueda asistida, bibliografía, corpus multiformato y extracción localizable.
4. **B4:** citas estructuradas IEEE, revisión afirmación–cita y Zotero según acceso probado.
5. **B6:** ampliar desde la generación unitaria B5.1 a agentes/lotes paralelos con dependencias, aceptación y apoyos acotados cuando haya permisos definidos.
6. **Ampliación posterior a P32 + B8:** preparación de campo, datos reales, análisis por enfoque, tablas/figuras y exportaciones reproducibles. Es trabajo de dominio nuevo; no basta con añadir prompts.
7. **B10:** pruebas integradas, seguridad, operación y documentación para interfaz. B9 se hace solo si un conector opcional obtiene permiso y aporta valor.

Para cada bloque: inspección del código actual → contrato y migración compatible → implementación → pruebas de caso real y adversario → OpenAPI/README/estado actualizados → verificación obligatoria. No iniciar todos los bloques a la vez ni informar progreso por número de archivos creados.

## 6. Definición de terminado del backend para frontend

El equipo puede decir «backend listo para frontend» solo cuando se cumplan **todas** estas condiciones:

- Los recorridos del §2 funcionan desde API con PostgreSQL y datos/documentos de prueba identificados; pruebas muestran permisos, errores, idempotencia, concurrencia y compatibilidad de proyectos anteriores.
- El comportamiento esperado de cada operación de la web está en OpenAPI y ejemplos: entrada, respuesta, estado, código de error y versión. El frontend no necesita calcular normas, decidir aprobaciones ni fabricar referencias.
- Las salidas de IA y las fuentes externas conservan procedencia y estado de aceptación. Resultados, cifras y figuras salen de datos versionados; falta de datos genera estado pendiente.
- Revisión del asesor y exportación comparten instantánea completa. El DOCX/PDF generado se abre y se verifica; no basta con obtener HTTP 200 o inspeccionar un archivo ZIP.
- Migraciones, respaldo/restauración y configuración del trabajador se prueban; secretos/permisos no quedan en el cliente. Toda integración opcional indisponible está señalada como tal y no se anuncia como funcional.
- `python3 -m core.grounding.audit_cli` y `python3 scripts/verify_project.py` terminan con exit code 0; se conservan salidas, tiempos y pruebas específicas. La aceptación metodológica del asesor y las decisiones UTP se registran separadas de la suite técnica.

**Cierre honesto:** si falta una de estas condiciones, el backend puede estar avanzado o listo para desarrollar una pantalla concreta, pero no se declara completo para todo el frontend. Es válido empezar una interfaz parcial cuando su contrato ya esté estable; esta definición expresa la preferencia del equipo de terminar el núcleo antes de concentrarse en ella.

## 7. Inventario de partida y frontera de la migración

El agente que programe no debe deducir que existe una capacidad porque aparece aquí. Antes de cada bloque anota `IMPLEMENTADO`, `PARCIAL`, `PENDIENTE`, `DEPENDIENTE_DE_PERMISO` o `DECISIÓN_ABIERTA` junto con ruta, símbolo, prueba y fecha de inspección. El inventario base está en [brechas backend](./inventario_brechas_backend.md) y [estado de producto](../07_desarrollo_prototipo/estado_version_producto.md).

| Pieza observada en el corte actual | Qué aporta | Lo que aún no permite afirmar |
|---|---|---|
| `backend/thesis/step_catalogue.py`, `services/step_contracts.py`, `services/steps.py`, `services/workflows.py`, `models/workflows.py` | P01–P32, modo dual (`LEGACY_SEQUENTIAL` / `CONFIGURABLE_GRAPH`), tareas `USR_...`, dependencias por grafo, prompts versionados y endpoints B5. `WorkflowTaskExecution` conserva el historial de resultados de tareas custom. | `execute` persiste JSON aportado por el cliente; no llama al LLM. P01–P32 siguen con contratos fijos; existe esquema de salida versionado para custom y ciclo de generación B5.1. Falta comprobar una llamada real y construir el snapshot íntegro de capítulo B1/B2. |
| `StepProgress`, `ChapterRevision`, `Chapter`, `ReviewEvent` | Avance, revisiones por paso y estados de revisión. | Snapshot íntegro del capítulo que coincida exactamente con la aprobación y la exportación. |
| `backend/thesis/api/projects.py` | API Ninja de proyecto, pasos, capítulos, fuentes, revisión, archivos, recorrido configurable B5 y rutas B5.1 para encolar, consultar, cancelar, aceptar y rechazar propuestas. | El adaptador Gemini existe, pero no se verificó una llamada real desde Django; el proveedor está deshabilitado por defecto. Faltan contratos web completos para editor, datos/resultados y figuras. |
| `mcp_server/prompts/` | Plantillas estáticas P01–P32 y prompts de rol. | Personalización/versiones por proyecto o ejecución multiagente autónoma. |
| Extracción, OCR, GROBID, pgvector y `DocumentJob` | Procesamiento local en algunos formatos y búsqueda de pasajes. | Lectura crítica automática de figuras/tablas, soporte homogéneo de todo formato o respuesta verificada de todo el corpus. |
| Exportación DOCX de borrador | Un archivo editable a partir de texto guardado. | Tesis institucional final, PDF verificado o correspondencia con una aprobación íntegra. |

La primera auditoría debe contrastar esta tabla con el árbol real. Cualquier cambio posterior al corte documentado se registra, no se sobrescribe en silencio. No crear modelos paralelos para una misma fuente, cita, documento o revisión sin explicar cómo se mantienen sincronizados.

## 8. Contratos funcionales por módulo

Las siguientes listas describen **comportamiento exigido al backend final**, no rutas ni modelos ya confirmados. En cada entrega el programador documenta entrada, salida, actor, regla, error, versión, migración y prueba. `docs/02_arquitectura_y_sistema/contratos_api_backend.md` conserva el inventario de rutas reales y grupos lógicos.

### 8.1 Proyectos, perfil y exploración

- Crear/listar/consultar proyectos del actor; modificar nombre/configuración con versión esperada. El perfil distingue carrera, modalidad de trabajo, enfoque y normas con fuente/fecha. Una modalidad de curso no hereda automáticamente trámites de título profesional.
- Guardar **todas** las ideas candidatas con procedencia, razones de viabilidad, estado y relación entre ideas derivadas. Mostrar cinco destacadas es una vista, no una restricción de almacenamiento ni generación. El usuario puede recuperar o combinar ideas.
- Mantener por separado título provisional, delimitación, problema, preguntas, objetivos, constructos o categorías y título confirmado. Un cambio de estas decisiones registra impacto sobre búsquedas, método, instrumento y capítulos ya revisados.
- Estado consultable para frontend: tareas disponibles, bloqueadas y pendientes de revalidación, con motivo legible y versión. No hacer que el navegador reconstruya el grafo desde códigos P.

### 8.2 Recorrido, prompts y método

- Seguir íntegramente el [contrato de recorrido y prompts configurables](./contrato_recorrido_y_prompts_configurables.md): borrador, diff, validación, publicación, versión usada en cada ejecución, restauración y aislamiento por proyecto.
- El usuario modifica texto, ejemplos, tono, orden y tareas opcionales. Un prompt personalizado no altera contratos Pydantic ni validadores de citas, datos y permisos. Una tarea puede planificarse antes y ejecutarse cuando tenga sus entradas reales.
- Definir dependencias por **datos y revisión exigible**, no por número de P. Auditar las dependencias ocultas en materializadores antes de adelantar P. Enviar un capítulo evalúa las tareas exigibles de la versión publicada, no todas las posiciones del catálogo heredado.
- La ruta cuantitativa admite hipótesis y variables cuando corresponda; la cualitativa admite preguntas y categorías sin VI/VD obligatorias; la mixta exige identificar componentes y punto de integración. No inferir el enfoque por la presencia de palabras en un prompt.
- PRISMA es una técnica/protocolo condicional; no es llave universal para crear la matriz de literatura. Likert, Alfa/Omega, V de Aiken e inferencia estadística también son condicionales. El piloto IEEE configura su estilo sin borrar lecturas APA históricas.

### 8.3 Búsqueda, referencias y biblioteca

- Preparar consultas reproducibles (fuente, ecuación, filtros, fecha, responsable); separar búsqueda ejecutada por backend, búsqueda manual del usuario y resultado importado. Para Scopus/WoS el recorrido base genera la consulta, enlaza el sitio oficial y recibe una exportación autorizada.
- Ingesta de identificadores y archivos: conservar archivo original, hash, proveedor, fecha, campos originales, normalización y errores por fila. Permitir deduplicación con propuesta y resolución humana; no fusionar automáticamente autores, ediciones o estudios distintos por título parecido.
- Documentos de biblioteca: versión original, permisos, estado de extracción, OCR selectivo y localizadores físicos (página, sección, hoja/celda, tabla). Markdown puede ser vista intermedia, nunca única fuente canónica de una hoja o figura.
- Preguntas al corpus deben devolver respuesta con pasajes/localizadores y nivel de acceso, o explicar por qué no se puede responder. La ausencia de un fragmento en el corpus cargado no prueba que una afirmación sea falsa en toda la literatura.
- Fichas de antecedentes muestran metadatos verificados, acceso real, citas/páginas, pertinencia para una función concreta, clasificación y limitaciones. Pueden prepararse en paralelo y presentarse al asesor en lote.

### 8.4 Editor canónico, citas y revisión de afirmaciones

- Definir una representación versionada del contenido del documento que el frontend pueda editar; Markdown o DOCX son proyecciones cuando corresponda. Los bloques/fracciones necesitan IDs/anclas estables para comentarios, citas y diff.
- Una ocurrencia de cita referencia una obra estructurada y, cuando se afirma respaldo textual, un pasaje localizado. Numeración IEEE y bibliografía se derivan del orden real de citas; un `[12]` escrito como texto libre no se trata como vínculo verificado.
- Auditar por separado (a) identidad bibliográfica y (b) relación entre afirmación concreta y texto inspeccionado. Devolver estado preliminar, pasajes, página, limitación de acceso y explicación. Una alternativa encontrada se muestra como propuesta de sustitución/reformulación con diff y aceptación explícita.
- Detectar referencias sin cita, citas sin referencia, duplicados, fuente retirada o pasaje que ya no coincide con la versión del archivo. Una edición del manuscrito o fuente puede dejar la evaluación anterior obsoleta; no preservar su etiqueta como vigente.
- El perfil de estilo propio, si se habilita, usa muestras autorizadas del tesista y solo adapta redacción. No modifica evidencia, cifras, norma IEEE ni autoría; puede borrarse y sus versiones quedan asociadas a propuestas generadas.

### 8.5 Asesoría y apoyos

- Crear una instantánea **completa** del capítulo/documento antes de enviarlo. `READY` apunta a contenido, citas, figuras, fuentes y versiones concretas; comentarios anclan esa instantánea. El asesor puede aprobar o solicitar cambios sobre lo que vio, no sobre la última revisión mutable.
- Mantener observaciones abiertas/resueltas, diffs entre revisiones, decisión, fecha, actor y motivo. La aprobación de asesor y un trámite/dictamen UTP son estados distintos. Un único asesor puede cubrir funciones temática y metodológica.
- Reducir trabajo repetitivo del asesor con bandeja de cambios, comentarios agrupados, comprobaciones previas y resumen de versiones; la decisión académica sigue siendo suya.
- Expertos y bibliotecarios son invitaciones puntuales a preguntas, búsquedas o materiales concretos: consentimiento/aceptación, vencimiento/revocación, permisos de recurso y respuesta versionada. No crear acceso global al proyecto ni convertir su aporte en aprobación automática. La administración institucional de guías está separada de tesis privadas.

### 8.6 IA web y multiagentes

- API de trabajos tipados: crear, consultar progreso, cancelar cuando sea seguro, ver propuesta/diff y aceptar/rechazar. Guardar actor, proyecto, versión de contexto/recorrido/prompt, proveedor, modelo, insumos permitidos, fuentes, salida, costo/uso cuando esté disponible y errores recuperables.
- Trabajos independientes (p. ej. antecedentes por región o fuente) pueden ejecutarse en paralelo y reunirse en una vista de lote. Los trabajos que dependen de un plan aprobado esperan su versión. Si cambia el contexto, el resultado queda obsoleto y requiere revisión antes de usarlo.
- Agentes potenciales: exploración de temas; estrategia de búsqueda; deduplicación; extracción; evaluación de evidencia; síntesis de antecedentes; coherencia metodológica; instrumentos; revisión de citas; respuesta a observaciones; análisis asistido de datos; redacción y figuras. Cada agente tiene contrato y permiso acotados; no son nuevos roles humanos obligatorios.
- Las salidas automáticas permanecen propuestas. Aceptación crea una nueva revisión auditada; rechazo no toca el manuscrito. El LLM nunca llama directamente a modelos Django ni publica un resultado por texto de prompt.

### 8.7 Campo, datos, análisis y hallazgos posteriores a P32

- Crear capacidades de dominio posteriores a P32 sin asignar códigos P nuevos por adelantado. Registrar protocolo, plan de análisis, versión de instrumentos, criterios de selección, consentimiento/permisos aplicables y evidencia de dictamen/exoneración cuando corresponda.
- Datos originales: carga y validación de archivos/registros, procedencia, esquema/diccionario, unidades, permisos, hash, fecha y versión de instrumento. Preservar originales y anotar exclusiones/correcciones; no editar la fuente en sitio para “limpiarla”.
- Cuantitativo: transformaciones declaradas, cálculo reproducible, supuestos, tablas/estadísticos elegidos por pregunta/diseño; mostrar tamaño de muestra efectivo y faltantes derivados de datos. No aceptar coeficientes o porcentajes escritos por IA como resultado calculado.
- Cualitativo: transcripciones/documentos con localizador, seudonimización, fragmentos, códigos/categorías, libro de códigos, decisiones de interpretación y citas de participantes auténticas con permisos. No inventar testimonios ni imponer coeficientes numéricos por defecto.
- Mixto: conservar resultados de ambos componentes y una unión explícita que indique qué evidencia produce cada inferencia integrada; registrar contradicciones y límites.
- Resultados, discusión, limitaciones, conclusiones y recomendaciones se vinculan a objetivos, análisis, figuras y antecedentes. La IA puede redactar borradores desde esas salidas, pero un hallazgo sin datos queda pendiente. Un ejemplo sintético usado en pruebas se etiqueta y nunca se exporta como hallazgo de un usuario real.

### 8.8 Figuras, tablas y exportación

- Una tabla/figura identifica dataset y versión, transformación/código, filtros, unidades, leyenda, fuente y revisión. La vista web puede recalcular al cambiar datos aceptados; el backend devuelve tanto resultado como procedencia resumida para un tooltip/panel.
- La exportación congela exactamente texto, citas numeradas, bibliografía, tablas/figuras, anexos y plantilla de la instantánea indicada. Si algo falta, devolver error accionable en vez de crear una tesis aparentemente lista.
- DOCX y PDF prioritarios, con inspección de contenido y renderizado de un caso representativo; declarar por separado LaTeX/BibTeX y campos activos Zotero solo tras pruebas propias. Una referencia IEEE correcta en PDF no implica que Word/LibreOffice pueda refrescar campos Zotero.
- El documento de entrega usa formato institucional aplicable versionado, no una plantilla inferida del audio. La plataforma puede preparar expediente y registrar similitud/actas, pero no produce por sí misma una aprobación institucional.

## 9. Superficie de API que el frontend debe recibir

Los nombres siguientes son **operaciones lógicas propuestas**, no afirmaciones sobre rutas existentes. Antes de crear una URL, comparar con `backend/thesis/api/projects.py`, `docs/02_arquitectura_y_sistema/contratos_api_backend.md`, OpenAPI generado y consumidores reales. Mantener `/api/v1/` y documentar cualquier transición compatible.

| Grupo | Lecturas necesarias | Mutaciones/trabajos necesarios | Respuesta mínima para el frontend |
|---|---|---|---|
| Sesión/proyecto | Identidad actual, proyectos propios, perfil, estado/versión. | Crear y editar proyecto/perfil, archivar según permiso. | IDs, permisos efectivos, `state_version`, siguiente acción/errores. |
| Ideas/método | Alternativas, versión publicada y borrador del recorrido, grafo, prompts efectivos. | Crear/editar ideas; editar/validar/publicar/restaurar método y prompts; preparar/guardar tarea. | Diff, `workflow_version_id`, dependencias faltantes, estado por tarea. |
| Literatura/corpus | Consultas, obras, archivos, jobs, páginas/pasajes y fichas. | Preparar búsqueda, importar referencias, subir/extraer documento, deduplicar, consultar corpus. | Procedencia, nivel de acceso, localizador, duplicados pendientes y error por fila. |
| Manuscrito/citas | Estructura/bloques, revisiones, ocurrencias, bibliografía y evaluaciones de soporte. | Guardar borrador, insertar/mover cita estructurada, solicitar auditoría, aceptar/rechazar diff. | Versión del texto, vínculo obra/pasaje, numeración IEEE derivada, estado de soporte. |
| Revisión/colaboración | Bandeja asesor, instantáneas, comentarios, decisiones, paquetes invitados. | Enviar, comentar, resolver, aprobar/observar, invitar/revocar apoyo. | Snapshot ID/hash, estados y permisos, ancla de comentario, motivo de bloqueo. |
| IA | Tipos de tarea permitidos, trabajos propios y propuesta. | Crear/cancelar trabajo, aceptar/rechazar salida, agrupar lote. | Estado/progreso, versión de contexto, costo disponible, fuentes y diff. |
| Campo/datos | Protocolo, instrumentos/versiones, autorizaciones, datasets, análisis. | Registrar permiso, cargar originales, transformar/calcular/codificar, revisar resultado. | Procedencia, parámetros, artefacto reproducible, estado de validación. |
| Figuras/exportación | Tablas/figuras con procedencia, exportaciones previas. | Recalcular, solicitar DOCX/PDF, descargar por permiso. | Snapshot IDs, transformaciones, formato real, enlace autorizado y advertencias. |

Para **cada** operación: esquema estricto, actor autorizado, recurso/tenant, precondiciones, tamaño/límite/paginación, respuesta de éxito, errores de dominio estables, `expected_version` cuando muta un agregado e idempotencia cuando repetir causa una creación o costo. En trabajos lentos devolver ID y estado; consultar/cancelar/descargar vuelve a comprobar permiso. Los errores deben distinguir validación, bloqueo por dependencia, falta de acceso, versión obsoleta, evidencia insuficiente y fallo de proveedor. El formato HTTP final puede evolucionar, pero no se permite que el frontend infiera el motivo a partir de un texto libre inestable.

### Ejemplo de contrato conceptual: tarea bloqueada

El objetivo es una respuesta equivalente a la siguiente; **no describe el JSON que hoy devuelve la API**:

```json
{
  "code": "PREREQUISITE_LOCKED",
  "task_id": "id-estable-de-tarea",
  "workflow_version_id": "version-publicada",
  "missing": [{"kind": "DATA", "source_task_id": "id-de-origen", "field": "criterios_de_busqueda"}],
  "can_save_draft": true
}
```

El cliente puede mostrar la tarea como planificada y conservar un borrador, pero no marcar una salida estructurada como completada. El agente debe fijar IDs/formato reales en contratos y pruebas antes de implementar la interfaz.

## 10. Datos, relaciones e invariantes que se deben diseñar

La tabla es un **modelo conceptual de información**. No ordena crear una tabla por fila. Reutilizar entidades existentes cuando puedan cumplir el contrato sin duplicación. Cualquier migración debe explicar lectura de proyectos legados y reversibilidad operativa.

| Agregado o registro | Identidad/vínculos mínimos | Invariante de integridad |
|---|---|---|
| Proyecto/perfil | Proyecto, titular, participantes, modalidad/enfoque, norma versionada. | Cada lectura/escritura se filtra por proyecto y permiso; perfil no determina automáticamente trámites no aplicables. |
| Recorrido y prompt | Proyecto, versión publicada/borrador, tarea estable, dependencia, prompt exacto y autor. | Grafo publicado sin ciclos; cambio nuevo no reescribe una versión usada. |
| Idea/decisión metodológica | Proyecto, opción origen, criterios, decisión, fecha y contexto. | Alternativa descartada se conserva y puede recuperarse; cambios señalan dependientes. |
| Obra/consulta/importación | Obra, identificadores, proveedor, consulta/archivo original, fila, revisión de duplicado. | Una obra puede tener metadatos de varias procedencias con discrepancias explícitas; no se atribuye acceso inexistente. |
| Documento/pasaje | Archivo/versión/hash, permiso, extracción, página/hoja/celda, texto y coordenadas cuando existan. | Cita/evaluación abre el original localizable; cambio de archivo obsoletiza pasajes derivados. |
| Manuscrito/snapshot/cita | Proyecto, bloque/revisión, versión de método, obra/pasaje, dataset/figura, actor. | La instantánea enviada/aprobada/exportada se reconstruye exactamente. |
| Propuesta de IA | Actor, tarea, prompt/contexto/modelo, fuentes, salida, estado de aceptación. | Propuesta sin aceptar no modifica estado canónico ni concede permisos. |
| Permiso/colaboración | Invitación, actor, recursos, acciones, vencimiento y revocación. | Acceso no excede el paquete concedido; respuesta de invitado no equivale a aprobación. |
| Dataset/análisis | Original/versionado, diccionario, procedimiento, código/parámetros, salida, validación. | Hallazgo numérico/textual se remonta a datos y transformación; original no se sobrescribe. |
| Figura/exportación | Spec visual, dataset/análisis, snapshot de documento, archivo/hash, formato. | Regenerar crea versión; descargar una exportación no lee datos nuevos del proyecto. |

No guardar únicamente etiquetas como `VERIFICADO` o `APROBADO` sin los IDs y evidencias que las sustentan. Si el producto usa hashes, indicar qué bytes/estructura cubren y cómo se comprueba su estabilidad. Retención/borrado de muestras de estilo, documentos y datos personales deben fijarse antes de invitar usuarios reales.

## 11. Permisos y decisiones por actor

El detalle exhaustivo está en [matriz de permisos](./matriz_permisos_y_cuentas_backend.md); esta tabla resume los casos críticos para el recorrido completo. Una función de asesoría temática y metodológica puede recaer en una sola cuenta.

| Acción | Tesista titular | Asesor asignado | Apoyo invitado | Servicio/IA |
|---|---|---|---|---|
| Editar proyecto, recorrido, borrador y datos propios | Sí, con versión/estado válido. | Lee y observa; edición directa solo si existe concesión explícita futura. | Solo material de tarea concedida; no edita canónico. | Nunca por iniciativa propia; propuesta bajo actor autenticado. |
| Publicar recorrido | Sí, según política de proyecto y sin reescribir aprobaciones. | Observa o da visto bueno si la política confirmada lo requiere. | No. | No. |
| Comentar y decidir capítulo | Puede enviar/responder observaciones; no autoaprobar como asesor. | Comenta y decide revisión exacta. | Devuelve informe de apoyo sin aprobación. | Prepara resumen/propuesta, sin decisión final. |
| Cargar/analizar datos | Sí, con permisos y ética aplicable. | Consulta/revisa material autorizado. | Solo subconjunto concedido. | Opera job con datos permitidos y resultado pendiente de aceptación. |
| Gestionar guía institucional | No por pertenecer a un proyecto. | No por ser asesor. | No. | Solo función administrativa autorizada y auditada, separada de tesis privadas. |

Pruebas negativas obligatorias: acceso cruzado entre proyectos; asesor que intenta publicar prompt sin concesión; invitado que solicita archivo ajeno al paquete; IA que incluye `user_id` falso; descarga de exportación privada con token ajeno; aprobación de capítulo con observaciones abiertas o versión obsoleta.

## 12. Escenarios de aceptación integrados para mostrar al profesor

Cada escenario se ejecuta sobre PostgreSQL y API/servicios reales; los datos de prueba son identificados y no se presentan como resultados de tesis genuina. Una prueba unitaria que solo compara constantes no sustituye el recorrido.

### Escenario A: recorrido editable con consecuencias reales

1. Crear proyecto y dos alternativas de tema; conservar una fuera de las destacadas.
2. Crear versión borrador del recorrido. Adelantar búsqueda exploratoria, editar prompt, agregar una tarea y publicar tras validación.
3. Guardar una tarea independiente sin completar todos los P anteriores; verificar que una tarea con dependencia real sigue bloqueada con motivo y `workflow_version_id`.
4. Ejecutar una propuesta de IA bajo la versión publicada, rechazarla y comprobar que no cambió contenido canónico.
5. Crear una versión nueva tras una observación del profesor; recuperar la anterior y comprobar que revisiones antiguas aún la referencian.

### Escenario B: antecedente y cita comprobable

1. Preparar ecuación Scopus/WoS, registrar que el usuario ejecutó la consulta fuera de TesisMCP e importar un archivo exportado; no atribuir al backend una búsqueda que no hizo.
2. Adjuntar un PDF permitido, extraer página/pasaje y crear ficha de antecedente con nivel de acceso exacto.
3. Insertar cita estructurada en un borrador; solicitar revisión afirmación–cita. Mostrar pasaje y localizador o `INSUFFICIENT_ACCESS` si solo hay metadatos.
4. Cambiar la fuente o la afirmación; demostrar obsolescencia de la evaluación anterior y propuesta de diff antes de sustituirla.

### Escenario C: asesor, datos reales de prueba y entrega

1. Preparar plan/instrumento y registrar estado ético aplicable; impedir avanzar a campo cuando falte una autorización requerida para ese caso.
2. Cargar un dataset **auténtico de prueba** (archivo local que efectivamente existe, con datos sintéticos claramente etiquetados si es una demo), conservar original y ejecutar transformación/análisis determinista. Reproducir cifra/tabla/figura desde ese archivo.
3. Crear resultados y conclusión que se vinculen a objetivo/datos; intentar añadir cifra inexistente y observar rechazo o estado pendiente.
4. Crear snapshot íntegro; asesor comenta, solicita corrección y aprueba una versión sin observaciones abiertas.
5. Exportar DOCX/PDF, abrirlos e inspeccionar que contenido, citas, tabla y figura corresponden al snapshot aprobado. Editar el proyecto después y demostrar que los archivos previos no cambian.

### Escenario D: ramas metodológicas

- Cuantitativa: variables/indicadores, instrumento y análisis coherentes con diseño; hipótesis solo si corresponde; coeficiente calculado desde respuestas piloto identificadas cuando se informe uno.
- Cualitativa: preguntas/categorías, selección y material textual localizable; sin error por no crear VI/VD, Likert o coeficiente.
- Mixta: componentes, datos/análisis de ambos y registro del paso de integración; no concatenar dos informes sin inferencia integrada.

El equipo registra petición, respuesta, IDs, versiones, estado final y archivo de prueba usado. La demostración ante el profesor puede usar una tesis ficticia, pero la interfaz/API debe rotular los datos sintéticos y ninguna documentación debe citarlos como evidencia de eficacia real.

## 13. Artefactos obligatorios en cada entrega de Antigravity

1. **Inventario previo:** archivos/símbolos reales tocados; brecha, requisito, estado anterior, prueba existente. Registrar hallazgos que contradigan esta documentación.
2. **Contrato:** rutas/esquemas OpenAPI, servicio compartido, permiso por actor, precondiciones, errores estables, semántica de versión e idempotencia. Añadir ejemplos verificables, no JSON inventado como si fuera salida actual.
3. **Migración:** descripción de nuevas entidades/campos, datos legados, lectura de revisiones antiguas, rollback operativo y prueba con proyecto creado antes de la migración.
4. **Implementación:** código en capas existentes (`api/`, `services/`, `models/`, `integrations/`, worker y MCP como fachada). Evitar lógica académica duplicada en router, prompt o frontend.
5. **Pruebas:** caso positivo, negativo, aislamiento, concurrencia, idempotencia, cambio de versión y recorrido integrado que corresponda. Proveedores externos simulados en tests se distinguen de una comprobación real de acceso; ninguna salida simulada se vende como integración activa.
6. **Documentación sincronizada:** `backend/README.md`, especificación/API, [estado verificable](../07_desarrollo_prototipo/estado_version_producto.md), [brechas](./inventario_brechas_backend.md) y diagramas afectados. Marcar `IMPLEMENTADO` solo después de ejecutar pruebas.
7. **Reporte de cierre:** resultados de comandos, tiempos/códigos de salida, capacidades demostradas, límites, bloqueos de permisos externos y siguiente bloque. No presentar porcentajes de “backend terminado” inferidos del número de archivos o endpoints.

La [puerta obligatoria de verificación](../../AGENTS.md) se ejecuta al cerrar una entrega de código; durante la implementación pueden usarse pruebas focalizadas. La suite técnica no sustituye evaluación de usabilidad, revisión del profesor, dictamen ético ni permisos de proveedores.

## 14. Decisiones abiertas con salida por defecto

| Decisión pendiente | Qué se puede construir ya | Qué no se debe afirmar hasta resolverla |
|---|---|---|
| Política de visto bueno del asesor cuando cambia un plan aprobado | Versiones, diff, detección de impacto y avisos. | Que publicar cualquier versión revalida automáticamente una aprobación anterior. |
| Reglas UTP por carrera/modalidad y plantilla final | Motor de reglas con procedencia/versionado; piloto IEEE configurado por acuerdo del equipo. | Que IEEE o un trámite específico aplica a toda UTP. |
| Proveedor/costo/retención de IA | Adaptador, jobs, aceptación, límites y prueba controlada. | Que existe generación real operativa si solo se probaron mocks. |
| Acceso Scopus/WoS | Búsqueda manual asistida e importación con procedencia. | Descarga, consulta API o texto completo automatizados. |
| Zotero y campos activos | Modelo de cita propio, importación bibliográfica y adaptador con autorización cuando exista. | Sincronización OAuth o refresco de campos en Word/LibreOffice sin prueba externa. |
| Formato exacto de datos/figuras por tesis | Modelo estructurado, transformaciones reproducibles y ejemplos por enfoque. | Que un único análisis sirve para toda disciplina o método. |
| Despliegue público | Configuración local reproducible, secretos, backups y prueba de restauración. | Servicio listo para usuarios reales sin seguridad/operación verificadas. |

Ninguna decisión abierta autoriza a Antigravity a inventar una norma, licencia, fuente o resultado. Si falta una decisión, implementar la capa extensible, registrar el bloqueo concreto y continuar con dominios independientes. Si el bloqueo afecta un recorrido esencial del §2, el backend todavía no satisface la definición de cierre del §6.
