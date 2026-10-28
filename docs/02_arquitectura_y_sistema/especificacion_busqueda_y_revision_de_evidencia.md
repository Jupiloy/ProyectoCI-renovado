# Especificación de búsqueda, lectura documental y revisión de afirmaciones

**Estado:** objetivo de producto y contrato funcional para planificación; no afirma que estas capacidades ya estén implementadas. **Actualizado:** 25/10/2026.

Este documento convierte tres necesidades del equipo en un flujo programable: (1) explorar ideas y hallar literatura relacionada; (2) permitir que el usuario use manualmente bases licenciadas como Scopus y Web of Science, sin requerir API; y (3) ayudar a comprobar si una fuente respalda la afirmación concreta que cita el borrador. También define cómo expertos, bibliotecarios y otros invitados pueden reducir trabajo dentro de un proyecto sin volverse participantes obligatorios.

**Implementación parcial posterior (corte B3.6, 26/10/2026):** la búsqueda peruana se expone por `GET /api/v1/projects/{id}/discovery/peru`; `SourceDocument` tiene identidad multi-proveedor; RIS/BibTeX/CSV se importan por `POST .../sources/import-bibliography`. B3.4 añade `SearchStrategy` versionado y `SearchExecution`, que registra una declaración manual; B3.5 guarda resultados seleccionados y relaciona fuentes importadas/seleccionadas con la ejecución mediante `SearchExecutionSource`. B3.6 añade decisiones humanas inmutables y versionadas sobre pares candidatos, con acciones para confirmar duplicidad, mantenerlos separados o designar explícitamente el registro preferido. Los metadatos enviados por el cliente se marcan no verificados; la procedencia no demuestra que se consultó Scopus/WoS ni que una exportación sea auténtica. Las decisiones no fusionan registros, trasladan citas ni borran procedencia. B3.5 pasó la puerta 7/7; la evidencia integral de B3.6 se presenta en el reporte de este corte. Consultar [guía de continuidad](./guia_continuidad_backend.md).

**Implementación B7 verificada:** fuentes PDF/DOCX/PPTX/XLSX conservan original/hash y estados de extracción; documentos Office generan segmentos recuperables con localizador propio. La búsqueda del corpus devuelve candidatos localizados, pero `EvidenceLink` y la revisión de citas existentes siguen anclados a `SourceExcerpt` de página PDF; ningún resultado Office pasa a ser evidencia académica confirmada automáticamente. Puerta integral B7 aprobada 7/7, 381.76 s, exit code 0. Ver [paquete B7](./paquete_b7_multiformato.md).

Para estado de código, inspeccionar [inventario de brechas](./inventario_brechas_backend.md), modelos, servicios y pruebas. Esta especificación describe la meta. No crear modelos, endpoints, agentes ni permisos antes de cotejar el código existente.

## 1. Propósito y resultado para el usuario

TesisMCP debe ayudar al tesista a pasar de una idea expresada en lenguaje común a una colección organizada de fuentes que pueda explorar, consultar y revisar con su asesor. Después debe permitir comprobar afirmaciones del manuscrito contra fuentes disponibles y mostrar evidencia localizable.

El valor no consiste solo en entregar una lista de títulos. La plataforma debe reducir tareas repetitivas —reformular búsquedas, copiar referencias, ordenar archivos, cotejar citas y aplicar observaciones— y permitir que el estudiante, asesor o especialista concentre su tiempo en decisiones académicas. La interfaz muestra qué procesó el sistema, qué encontró, qué no pudo comprobar y qué decisión sigue pendiente.

La meta de reducir tiempo es un objetivo de diseño, no un resultado demostrado. No afirmar porcentajes, ahorro ni eficacia hasta medir tareas comparables con usuarios y registrar método, muestra y resultados.

## 2. Conceptos que no deben confundirse

| Concepto | Significado en TesisMCP | No significa |
|---|---|---|
| Exploración de literatura | Descubrir temas, términos, autores y trabajos posiblemente relacionados con una idea. | Revisión sistemática completa ni prueba de que un tema sea novedoso. |
| Búsqueda reproducible | Consulta, filtros, base, fecha y criterios guardados para poder repetir o explicar una búsqueda. | Que TesisMCP haya ejecutado la consulta en una base cerrada. |
| Resultado bibliográfico | Registro con metadatos y procedencia. | Lectura del texto completo o evidencia para una afirmación. |
| Documento disponible | Texto completo abierto, aportado por el usuario o accesible por una ruta permitida, con nivel de acceso registrado. | Permiso para redistribuirlo o usarlo fuera de las condiciones del proveedor. |
| Coincidencia semántica | Una fuente comparte conceptos o vocabulario con una afirmación. | Que la fuente la respalde. |
| Metadatos verificados | Se cotejó identidad bibliográfica con una fuente confiable. | Que el contenido de la obra sustente la cita. |
| Evaluación automática de respaldo | Propuesta de relación entre una afirmación y pasajes de una fuente. | Aprobación académica ni verificación infalible. |
| Aprobación humana | Una persona autorizada confirma una decisión para una revisión y versión concretas. | Garantía universal sobre toda la obra o futuras versiones. |

## 3. Flujo del tesista

### 3.1 Explorar una idea sin cerrar prematuramente el tema

1. El tesista describe la idea, problema o aplicación en lenguaje natural.
2. TesisMCP conserva esa formulación y propone conceptos centrales, sinónimos, traducciones, tecnologías, contextos, poblaciones y enfoques cercanos. Debe distinguir los conceptos explícitos de las expansiones sugeridas por IA.
3. Puede consultar fuentes abiertas conectadas y la web según las capacidades realmente disponibles. Cada consulta y proveedor se registra. Las búsquedas independientes pueden ejecutarse en paralelo.
4. La interfaz presenta trabajos relacionados y variantes de tema con la razón de relación, metadatos disponibles, enlaces y nivel de acceso. Una similitud alta solo prioriza lectura; no demuestra pertinencia ni calidad.
5. El tesista conserva todos los candidatos, derivados y descartados provisionalmente con sus razones. La interfaz puede destacar cinco opciones viables, pero no impone un límite de cinco.
6. El estudiante y el asesor deciden si una alternativa merece convertirse en tema delimitado. Una etiqueta de “posible vacío” siempre indica la búsqueda, fecha, corpus y filtros que la sustentan; nunca afirma que no exista literatura en general.

La exploración amplia es distinta de una búsqueda formal de antecedentes. No aplicar filtros temporales, geográficos o metodológicos estrictos durante la ideación salvo que el usuario los elija. Mostrar y explicar los filtros activos.

### 3.2 Preparar búsqueda formal y uso manual de Scopus/WoS

La búsqueda en Scopus o Web of Science **no debe requerir API para que el producto sea útil**. La primera experiencia es asistida y manual:

1. TesisMCP propone bloques conceptuales, sinónimos y ecuaciones; explica qué representa cada bloque y permite editarlos.
2. El usuario selecciona la base y revisa/ajusta la sintaxis. La plataforma guarda la ecuación exacta, campos, filtros, fecha, base declarada, versión del tema y criterios de inclusión/exclusión.
3. Un enlace abre la búsqueda oficial de Scopus o WoS. El usuario inicia sesión en su propio contexto y ejecuta/ajusta la búsqueda allí. TesisMCP no pide ni guarda contraseñas institucionales.
4. El usuario exporta los resultados desde la base y los importa a su proyecto (RIS, BibTeX, CSV u otro formato solo después de comprobarlo). También puede registrar una referencia manual con enlace/DOI.
5. TesisMCP muestra filas aceptadas, errores, campos ausentes, posibles duplicados y discrepancias; conserva el archivo de importación y la procedencia declarada. No convierte un registro importado en “leído” o “verificado”.
6. El usuario puede pedir a un asesor o bibliotecario que revise la estrategia y los resultados importados.

La plataforma puede buscar automáticamente en fuentes abiertas para descubrimiento y cotejo bibliográfico cuando exista un adaptador funcional y permitido. Una API de Scopus/WoS puede añadirse como conector opcional si se demuestra el entitlement y el uso permitido; **no es prerrequisito de la búsqueda asistida, de la importación ni de la lectura de archivos**. Automatización de interfaz no forma parte del flujo base ni puede eludir controles, cuotas o términos del proveedor.

### 3.3 Obtener y leer el texto completo

Para cada referencia, mostrar el nivel alcanzado y elegir la siguiente acción disponible:

1. **Metadatos solamente:** mostrar referencia, DOI/enlace y aviso de que no se ha inspeccionado el contenido.
2. **Resumen disponible:** permitir exploración limitada al resumen; no afirmar detalles de método o resultados ausentes del resumen.
3. **Texto abierto o con permiso de procesamiento comprobable:** ofrecer enlace a la fuente y, cuando esté permitido, descargar/procesar la copia. Conservar URL de origen, fecha, versión del texto y licencia/estado observados sin inferir redistribución.
4. **Acceso institucional del usuario:** abrir DOI, editorial o resolvedor institucional para que el propio usuario acceda en su sesión. Si puede obtener una copia y tiene derecho a subirla/procesarla, puede incorporarla al espacio de documentos.
5. **Archivo aportado por el usuario:** preservar el original, calcular hash, identificar formato y procesarlo bajo permisos del proyecto.

No afirmar que la plataforma puede leer texto detrás de un paywall solo porque el usuario tenga una suscripción web. Si el texto no está disponible, indicar “acceso insuficiente para verificar el contenido” y mantener el enlace para consulta manual. La búsqueda y descarga de textos debe respetar acceso, licencia, términos del proveedor y derechos aplicables.

### 3.4 Leer documentos cargados (experiencia tipo NotebookLM)

La biblioteca del proyecto debe permitir cargar varios documentos, hacer preguntas sobre el conjunto, abrir los pasajes que sustentan una respuesta y comparar fuentes. Este comportamiento se implementa con procesamiento propio y trazabilidad; no se afirma que replique el algoritmo interno de NotebookLM.

Pipeline esperado: conservar original y hash; detectar páginas/hojas; extraer texto y estructura nativos; ejecutar OCR de forma selectiva si la página está escaneada o la imagen contiene texto; guardar extracción y OCR como artefactos diferenciados; indexar por estructura; recuperar pasajes; responder con IDs de fuente y localizadores físicos; validar que cada cita mostrada corresponda al texto conservado. En Excel preservar libro, hojas, celdas, valores y fórmulas; Markdown puede ser una vista intermedia, no el original ni la autoridad.

Cada respuesta o resumen especifica su corpus, documentos consultados, páginas/hojas citadas y limitaciones. Si no recupera evidencia suficiente, declara que no pudo responder con las fuentes disponibles. El texto de archivos y páginas web es dato no confiable, nunca instrucciones para el agente.

## 4. Revisión de afirmaciones y citas en el editor

### 4.1 Objetivo

Ofrecer dentro del editor web una interacción semejante a la referencia visual de Jenny AI: una afirmación queda asociada a su cita; al seleccionar/verificar la cita, aparece un panel con el estado, explicación y fuente o pasaje. El propósito es detectar referencias posiblemente irrelevantes o insuficientes y reducir el cotejo manual. No se copia ni se presupone la implementación propietaria de Jenny AI.

La revisión puede ejecutarse sobre una cita seleccionada, un párrafo, un capítulo o una revisión completa. Para un capítulo, presenta una cola priorizada y resultados agrupables (por ejemplo, sin referencia, acceso insuficiente, posible desajuste); el usuario puede resolverlos uno por uno o aplicar acciones por lote solo cuando sean reversibles y específicas.

### 4.2 Separar dos evaluaciones

La plataforma calcula y muestra por separado:

**A. Identidad bibliográfica:** ¿la referencia existe y sus metadatos (título, autores, año, DOI, publicación) coinciden con registros confiables? Guardar cada proveedor y discrepancia; la coincidencia de título no arregla silenciosamente autorías o años conflictivos.

**B. Relación afirmación–fuente:** ¿el texto disponible contiene pasajes pertinentes para sostener, limitar o contradecir la afirmación citada? Esta evaluación exige texto inspeccionable y localizadores. DOI válido, resumen coincidente, número de citas o similitud vectorial no bastan.

Una cita puede pasar A y fallar B. Si no se obtuvo texto suficiente, B queda como no verificable por acceso, aunque A esté resuelta.

### 4.3 Unidad de análisis y estados

Dividir, cuando haga falta, una oración con varias proposiciones en afirmaciones atómicas que conserven sujeto, población, periodo, condición, dirección, magnitud y grado de certeza. Mostrar el texto original y permitir corregir la segmentación antes de generar cambios. Las cifras, causalidad, universalidad y población son componentes explícitos de la afirmación y deben cotejarse individualmente.

La evaluación automática preliminar usa exactamente estos estados relacionales:

| Estado | Uso |
|---|---|
| `SUPPORTS` | El pasaje inspeccionado respalda la afirmación dentro del alcance y condiciones expresados. |
| `PARTIAL_SUPPORT` | Solo parte de la afirmación está apoyada o la fuente exige matizar su alcance. |
| `CONTRADICTS` | El pasaje informa evidencia incompatible con la afirmación o su dirección. |
| `UNRELATED` | El texto inspeccionado trata otro asunto o no sostiene la proposición citada. |
| `INSUFFICIENT_ACCESS` | No hay texto suficiente; solo hay metadatos, resumen insuficiente, fragmento incompleto o error de extracción. |
| `NOT_ASSESSED` | La comprobación todavía no se ejecutó o no produjo una evaluación interpretable. |

El estado de relación no es el estado de aprobación. Cada evaluación también tiene un flujo separado, como `PROPOSED`, `ACCEPTED_BY_STUDENT`, `REVIEWED_BY_ADVISOR` o `DISMISSED`, asociado a una revisión inmutable y un actor. “Aceptado” significa que esa persona acepta la acción/documentación mostrada; no certifica la verdad completa de la fuente.

### 4.4 Evidencia y explicación mostrada

Cada evaluación debe guardar y presentar:

- texto exacto de la afirmación evaluada y su ancla en la revisión;
- ocurrencia de cita y referencia versionada;
- archivo/edición/hash o registro bibliográfico utilizado;
- método y nivel de acceso (texto completo, OCR, extracto, resumen, metadatos);
- pasaje textual breve y localizador físico exacto (página; o sección/tabla/hoja/celda cuando aplique);
- explicación concreta de qué parte apoya, limita, contradice o no corresponde;
- incertidumbre/limitaciones del extractor o evaluación y versión del proceso/modelo;
- fecha, entradas y fuentes consultadas.

Si no se inspeccionó el texto completo, no emitir un juicio sobre contenido no visible. Si la paginación física no está disponible, mostrar el localizador que sí existe y etiquetar la limitación; no inventar páginas. Las citas textuales deben ser breves y solo las necesarias para que el usuario compruebe el resultado.

### 4.5 Candidatos alternativos y cambios

Cuando una cita resulte `UNRELATED`, `PARTIAL_SUPPORT` o `INSUFFICIENT_ACCESS`, TesisMCP puede buscar literatura relacionada a partir de los conceptos de la afirmación. Puede usar fuentes abiertas disponibles y resultados que el usuario importó desde Scopus/WoS. Debe explicar por qué cada candidata parece pertinente, mostrar su propio nivel de acceso y, para sugerir respaldo, recuperar un pasaje localizable que trate la proposición.

La interfaz ofrece, como propuestas distintas: conservar cita; revisar fuente original; seleccionar candidata; reescribir o acotar afirmación; retirar afirmación/cita; dejar pendiente. No reemplazar referencias, reformular afirmaciones ni renumerar citas IEEE en el documento canónico sin una acción explícita del tesista. El asesor revisa cambios según el flujo normal del proyecto. Guardar el antes/después y su relación con fuentes, evaluación y actor.

No sugerir un candidato como sustituto de evidencia basándose solo en título, palabras compartidas, resumen, conteo de citas, factor de impacto o clasificación automática. Si no hay pasaje accesible, la sugerencia se presenta solo como “lectura candidata”, no como fuente que respalda el texto.

## 5. Asesores y apoyos invitados: participación concreta

### 5.1 Participantes centrales y capacidades

Tesista titular y asesor asignado son los participantes centrales. Las funciones de asesoría temática y metodológica son capacidades separables que pueden asignarse a la misma persona. El permiso de aprobar una revisión corresponde al asesor asignado conforme a la política del proyecto; una especialidad declarada no da permiso por sí sola.

Experto invitado, bibliotecario o evaluador no son roles universales obligatorios. Si el caso de uso se implementa, representan **invitaciones a una tarea concreta y a recursos expresamente compartidos**, con permisos limitados y auditados. No convertir las categorías en acceso a todos los proyectos.

### 5.2 Paquetes de colaboración que reducen trabajo manual

**Revisión temática/metodológica puntual:** el asesor o tesista prepara una pregunta y selecciona versiones/pasajes relevantes. El experto recibe un paquete con contexto declarado, pregunta, criterios y documentos autorizados; puede responder con comentarios anclados y una lista de observaciones. Sus respuestas quedan como propuestas. El tesista decide qué incorporar y el asesor asignado conserva la aprobación académica del capítulo.

**Consulta a bibliotecario:** el sistema prepara el tema, bloques de sinónimos, ecuación, bases, campos, fecha/filtros y archivos importados. El bibliotecario puede corregir estrategia, sugerir vocabulario y señalar cobertura o duplicados; registra la recomendación y su alcance. El usuario ejecuta manualmente Scopus/WoS en el recorrido base, importa resultados y decide su inclusión. La plataforma evita volver a transcribir ecuaciones y referencias ya guardadas.

**Administración institucional:** una extensión separada puede mantener documentos institucionales versionados (guías, formatos, líneas de investigación) y asignarlos a carreras/periodos tras validación de una persona autorizada. No implica que el administrador lea o edite tesis individuales; el acceso a contenido del proyecto debe concederse por separado y quedar auditado.

**Servicios externos:** búsqueda abierta, resolutores de texto completo, Zotero, OCR, conversores y modelos son conectores, no personas ni roles. El usuario puede activar una capacidad permitida; la plataforma muestra proveedor, datos enviados/recibidos, estado, permisos y errores. No bloquear el flujo si un proveedor falla: permitir importación o carga compatible.

### 5.3 Invitación y permisos mínimos

Un invitado recibe invitación con proyecto, tarea/alcance, expiración o duración, recursos visibles y permisos explícitos. Debe aceptarla autenticado antes de obtener acceso. La autorización se comprueba en el backend en cada consulta, archivo, job y descarga. El invitado no ve otros capítulos, muestras de escritura, datos personales ni documentos fuera del paquete compartido. No puede editar contenido canónico, cambiar método, aprobar capítulos, invitar a otros ni añadir integraciones salvo autorización explícita independiente.

Permisos candidatos para diseño (no roles de base de datos ya implementados): `VIEW_SHARED_MATERIAL`, `COMMENT_SHARED_MATERIAL`, `SUGGEST_SEARCH_CHANGE` y `SUBMIT_TASK_RESPONSE`. El agente debe inspeccionar si el modelo actual puede expresarlos; no ampliar `ProjectParticipant.Role` ni añadir una tabla por anticipado sin revisar el dominio y justificar la migración. Revocar invitación invalida accesos futuros, pero conserva autoría y eventos históricos.

### 5.4 Reducir esfuerzo sin perder responsabilidad

Dar herramientas de productividad a cada participante:

- tareas por lote, listas de revisión y observaciones agrupadas;
- comparación de versiones y anclas que saltan al pasaje concreto;
- plantillas/rúbricas configuradas por proyecto y vinculadas a su fuente;
- consultas, ecuaciones, filtros, importaciones y revisiones guardadas para reutilizar;
- deduplicación revisable, aplicación controlada de observaciones y sugerencias con diff;
- panel de pendientes con responsable, bloqueo, fecha/evento y siguiente acción;
- tareas asíncronas con progreso, cancelación, error y reintento visibles.

La automatización puede preparar, ordenar, comparar y proponer. La elección de tema/fuentes, interpretación, modificación del argumento y aprobación se mantienen en manos del actor autorizado. No hacer que un invitado repita trabajo que la plataforma ya registró; cada aporte debe conectarse a un objeto y versión concretos.

## 6. Contratos lógicos mínimos

Estos son grupos lógicos, no nombres ni endpoints implementados. Consolidarlos con las rutas y modelos existentes antes de programar.

| Operación | Entrada relevante | Resultado y persistencia |
|---|---|---|
| Explorar idea | Tema provisional, conceptos explícitos, expansiones aceptadas, filtros y versión de contexto. | Resultados/candidatos con motivo de relación, procedencia, estado de acceso y consulta. |
| Preparar búsqueda externa | Fuente/base elegida, ecuación editable, campos, filtros, criterios y versión del tema. | Consulta reproducible y enlace a la base; sin afirmar que Scopus/WoS fue consultado automáticamente. |
| Importar resultados | Archivo, proveedor declarado, consulta/fecha opcionales. | Informe por fila, campos disponibles, duplicados, discrepancias y vínculo con la búsqueda. |
| Resolver texto | Referencia, destino permitido, fuente de acceso y elección del usuario. | Enlace/archivo y nivel de acceso; cualquier descarga pasa controles de origen, licencia y SSRF. |
| Procesar documentos | Archivo/URL permitido, opciones OCR, actor, proyecto. | Job, original/hash, extractos estructurados y localizadores con versión del extractor. |
| Preguntar al corpus | Pregunta, IDs/versiones de documentos y alcance. | Respuesta con pasajes/fuentes localizables y limitaciones; vacío explícito si no hay sustento. |
| Revisar afirmación/cita | ID de revisión, ancla/afirmación, ocurrencias de citas y corpus permitido. | Evaluación preliminar tipada con estado, pasajes y nivel; nunca muta el manuscrito. |
| Proponer sustitución o edición | Evaluación, fuente candidata, pasaje y edición propuesta. | Diff/propuesta en estado pendiente; aceptación explícita crea una nueva revisión. |
| Invitar apoyo | Email/usuario, tarea, recursos permitidos, permisos, vencimiento y actor. | Invitación de un uso con aceptación, revocación y eventos; no membresía general implícita. |
| Responder tarea invitada | Invitación aceptada, tarea, comentario/ancla/resultado. | Aporte aislado ligado a proyecto, paquete y versión; revisión por tesista/asesor. |
| Registrar revisión humana | Evaluación, decisión, actor y versión. | Evento inmutable separado del juicio automático. |

Usar trabajos asíncronos para búsquedas amplias, extracción, OCR, análisis de citas y documentos largos. Consultas pequeñas/manuales pueden ser síncronas si ya existe una ruta compatible. Todas las operaciones deben definir actor, scope, idempotencia/concurrencia, errores y retención.

## 7. Requisitos de aceptación

La capacidad no se declara implementada solo por tener un prompt, un agente o una ruta. Debe demostrarse el comportamiento observable correspondiente:

1. **Búsqueda sin API:** crear ecuación editable de Scopus/WoS, guardar base/fecha/filtros y abrir la consulta; completar el flujo importando exportación de usuario sin token API.
2. **Exploración amplia:** obtener candidatos relacionados a partir de conceptos y explicar relación; conservar alternativas fuera de los cinco destacados.
3. **Procedencia:** cada resultado distingue proveedor declarado, adaptador realmente usado, importación manual y documento subido; no reetiquetar OpenAlex como Scopus.
4. **Acceso parcial:** con solo metadatos/resumen, bloquear juicio de contenido no inspeccionado y mostrar `INSUFFICIENT_ACCESS` cuando corresponda.
5. **Preguntas documentales:** respuesta sustentada en documento debe abrir el pasaje/página/hoja correcta; sin pasaje no se muestra como evidencia confirmada.
6. **Afirmación bien respaldada:** la evaluación guarda afirmación y pasaje exactos, emite estado preliminar y mantiene separadas identidad bibliográfica y relación semántica.
7. **Desajuste y reemplazo:** una cita irrelevante puede producir candidata, explicación y pasaje; no cambia texto ni cita hasta aceptación del tesista. El asesor ve el cambio en la revisión posterior.
8. **Contradicción/parcialidad:** mostrar evidencia que limita o contradice; no favorecer solo pasajes de apoyo ni borrar desacuerdos.
9. **Invitado aislado:** solo lee materiales compartidos para la tarea; acceso a otro proyecto/archivo, aprobación, edición canónica o invitación no autorizada falla en backend y queda cubierta por prueba.
10. **Tarea repetitiva:** un flujo de revisión en lote permite resolver varios elementos sin perder identidad, actor, evidencia ni control individual de acciones irreversibles.
11. **Cambio de contexto:** si cambia pregunta, afirmación, fuente o documento, la evaluación anterior permanece ligada a su versión y se marca obsoleta para nueva revisión.
12. **Tiempo y esfuerzo:** en evaluación con usuarios se registra tarea comparable, tiempo activo, pasos repetidos, correcciones y errores; reportar resultado real y limitaciones. Hasta entonces decir “diseñado para reducir”, no “reduce X%”.

## 8. Orden sugerido de construcción

El orden orienta las dependencias de este módulo. P01–P32 y capítulos 1–7 son la base heredada; el alcance final del backend incluye las etapas empíricas y de cierre definidas en el [criterio de backend listo para frontend](./criterio_backend_listo_para_frontend.md):

1. Auditar código, permisos y tratamiento documental existente; inventariar qué está implementado, parcial o pendiente.
2. Garantizar registro/importación de búsqueda, procedencia multi-proveedor y estado de acceso; documentar ecuación manual de bases licenciadas.
3. Mejorar extracción y consulta de corpus con localizadores confiables antes de usarla como prueba de afirmaciones.
4. Implementar vínculo afirmación–cita–fuente y evaluaciones preliminares con estados/limitaciones; diseñar la tarjeta del editor y el historial de cambios.
5. Añadir acciones de aceptación/rechazo del tesista y revisión del asesor sobre instantáneas; preservar exportación reproducible.
6. Incorporar invitaciones acotadas si existe caso de uso acordado; diseñar permisos, expiración, aislamiento y revocación antes de exponerlo.
7. Evaluar proveedores/APIs licenciados solo si agregan cobertura necesaria y existe permiso probado; nunca bloquear con ello el flujo manual.
8. Medir esfuerzo/tiempo y calidad de evidencia con usuarios antes de anunciar beneficios cuantificados.

Los hitos deben integrarse con B0–B10 del plan general y no duplicar modelos/rutas existentes. Una decisión o permiso no relacionado no debe detener trabajo independiente.
