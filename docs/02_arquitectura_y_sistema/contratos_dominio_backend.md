# Contratos de dominio del backend

**Estado:** contratos de comportamiento objetivo; lo existente se identifica por separado. **Actualizado:** 25/10/2026.

Los contratos concretos Pydantic de P01–P32 y sus campos permanecen en [Contratos Pydantic y validadores](../03_metodologia_y_prompts/contratos_pydantic_y_validadores_mvp.md). Este documento añade las reglas transversales que deben observar servicios, API web y MCP. No duplica los esquemas ejecutables.

## Actores y alcance de autorización

| Actor/capacidad | Acceso objetivo | Regla |
|---|---|---|
| Tesista titular | Configurar proyecto, proponer temas, cargar fuentes, editar borradores, aceptar/rechazar propuestas de IA, enviar revisión y exportar. | Solo en sus proyectos; decisiones canónicas explícitas y versionadas. |
| Asesor asignado | Consultar las versiones presentadas, comentar, solicitar cambios, resolver/emitir decisiones y revisar vínculos de evidencia. | No edita silenciosamente la copia del tesista; aprobación identifica una instantánea exacta. Puede cumplir asesoría temática y metodológica. |
| Administrador de plataforma | Operación técnica mínima y soporte. | No es evaluador académico ni obtiene acceso indiscriminado al contenido por defecto. Diseño de break-glass/auditoría es decisión de seguridad. |
| Integración/agente | Ejecutar una capacidad autorizada con contexto de proyecto. | No es usuario académico ni tiene permisos propios; actúa bajo el actor autenticado y scopes concedidos. |
| Experto/bibliotecario invitado | Revisar una tarea delimitada y materiales compartidos mediante una invitación aceptada. | No es un rol universal ni tiene acceso por defecto. Sus capacidades se conceden por tarea/recurso; no puede editar ni aprobar el manuscrito canónico. Inspeccionar el modelo actual antes de diseñar el grant. |
| Mantenedor de configuración institucional | Publicar/retirar versiones de guías, plantillas y reglas institucionales tras autorización. | Capacidad administrativa separada de la membresía académica; no da lectura automática a tesis privadas. |

La identidad se resuelve en el servidor. Un `user_id`, email o rol elegido por el prompt no es prueba de identidad ni de autorización. Los permisos se vuelven a validar en cada operación, incluso si el agente ya obtuvo contexto.

## Ciclo de vida de proyecto, paso y capítulo

### Estados de capítulo

Los estados actuales documentados son `DRAFT`, `READY`, `CHANGES_REQUESTED` y `APPROVED`. La FSM existente se describe en [sistema de comentarios y revisión](../05_modulo_colaborativo_asesor/sistema_comentarios_y_revision.md). El objetivo conserva estas transiciones con controles:

| Transición | Actor | Precondiciones objetivo | Resultado |
|---|---|---|---|
| `DRAFT → READY` | Tesista titular | Existe instantánea completa del capítulo; contenido no vacío; requisitos configurados cumplidos; versión aún vigente. | Crear envío inmutable, notificar/mostrar al asesor. |
| `READY → CHANGES_REQUESTED` | Asesor asignado | Revisión/instantánea indicada; registrar decisión y observaciones. | Nueva tarea para tesista; conservar la versión revisada. |
| `READY → APPROVED` | Asesor asignado | La instantánea coincide con la que vio; sin comentarios abiertos requeridos; prerrequisitos configurados. | Guardar ID/hash de instantánea aprobada y evento. |
| `CHANGES_REQUESTED → DRAFT` | Tesista titular | Crear una nueva versión. | Comentarios anteriores conservan ancla histórica. |
| `APPROVED → DRAFT` | Asesor asignado o actor según política confirmada | Reapertura explícita con motivo y auditoría. | La aprobación previa permanece en historial; no mutar el snapshot anterior. |

**Brecha actual importante:** la revisión por paso, el `submit_chapter` y el ensamblado de exportación no garantizan por sí solos un snapshot completo coincidente. La entrega B1 debe resolver esto antes de declarar confiable la aprobación/exportación.

### Dependencias y trabajo adelantado

- P01–P32 conserva el catálogo actual como compatibilidad de datos y contratos.
- Las dependencias futuras deben representarse como grafo versionado y validarse sin ciclos.
- Puede adelantarse como borrador una búsqueda bibliográfica independiente si sus criterios quedan registrados.
- Un resultado dependiente de pregunta, población, método o variables debe señalar la versión de contexto usada y pasar revalidación cuando cambie esa decisión.
- No exigir aprobación del capítulo anterior para una tarea independiente salvo que una regla aprobada lo requiera. En cambio, no presentar como final un capítulo cuyo fundamento aprobado cambió.
- La lista “cinco temas viables” es presentación priorizada, no límite de candidatos. Guardar opciones, criterios, evidencia, estado, descarte provisional, razón y posibilidad de recuperación.

## Contrato común de una operación de dominio

Cada caso de uso debe definir:

1. **Actor y scope:** usuario autenticado, proyecto, rol/capacidad y propiedad del recurso.
2. **Precondiciones:** estado, versión, permisos, prerrequisitos, niveles de evidencia y configuraciones aplicables.
3. **Entrada tipada:** campos, nulabilidad, tamaño/formato y validaciones cruzadas.
4. **Efecto:** entidades creadas/actualizadas, evento de auditoría y transacción.
5. **Salida:** IDs/versiones, estado, avisos y procedencia.
6. **Errores estables:** código de dominio, explicación segura, posibilidad de reintento y versión actual si hay conflicto.
7. **Idempotencia/concurrencia:** clave idempotente cuando una repetición puede duplicar efectos; expected version en escrituras concurrentes.
8. **Criterios de aceptación:** resultado observable y caso negativo que demuestre permisos/reglas.

## Operaciones del dominio y aceptación mínima

| Caso de uso | Contrato mínimo | Criterios de aceptación mínimos |
|---|---|---|
| Crear proyecto | Actor titular, nombre opcional/tema provisional, configuración inicial. | No requiere título definitivo; proyecto y titular vinculados; actor ajeno no puede leerlo. |
| Explorar/guardar tema | Contexto del estudiante, candidatos, fuente/razón, criterios y estado; versión esperada. | No restringe el total a cinco; conserva descartados y razones; duplicados/derivaciones trazables; escritura conflictiva no sobrescribe. |
| Preparar/guardar paso | Proyecto, `step_code`, contexto/versiones, salida tipada, Markdown/árbol de documento, IDs de fuentes, expected version e idempotency key. | Esquema y reglas cruzadas validados; solo se materializan IDs autorizados; guardar dos veces con misma clave/contenido no duplica; conflicto deja DB intacta. |
| Modificar metodología/prompt | Versión origen, propuesta diff, dependencias, explicación, aprobador. | No cambia versión publicada ni proyecto activo hasta validación y publicación autorizada; historial/reversión comprobables. |
| Importar/reconciliar referencias | Archivo original, formato, proveedor declarado, consulta/fecha opcionales, filas normalizadas. | Reporta importadas/rechazadas/duplicadas; mantiene procedencias múltiples; nunca crea identificadores de otro proveedor ficticios. |
| Preparar búsqueda licenciada manual | Base elegida, ecuación editable, campos, filtros, criterios, versión de tema. | Persiste consulta reproducible y enlace al sitio oficial. No declara que consultó Scopus/WoS ni necesita una API. |
| Consultar corpus de documentos | Pregunta, fuentes/documentos autorizados y versiones procesadas. | Respuesta basada en pasajes recuperados con localizadores. Si no hay pasaje suficiente, informa falta de sustento. |
| Vincular Zotero | Usuario, scopes mínimos, biblioteca/colección e IDs de items. | Estado/revocación visibles; sincronización no borra silenciosamente cambios; referencias aprobadas mantienen snapshot. Campo activo exportado solo se anuncia tras prueba real. |
| Ingresar documento | Actor, archivo, hash, formato, permisos, resultado de extracción/OCR/trabajo. | Original preservado; job autorizado; errores visibles; texto conserva página/hoja/celda; archivo malicioso o fuera de límite rechazado. |
| Crear vínculo de evidencia | Revisión, afirmación, fuente/extracto/localizador, actor. | Proyecto/revisión/fuente coinciden; procedencia inmutable; estado distingue candidato y revisión humana. |
| Evaluar cita frente a afirmación | Revisión/ancla, afirmación, ocurrencia de cita, documentos disponibles y proceso/versiones. | Emite relación preliminar (`SUPPORTS`, `PARTIAL_SUPPORT`, `CONTRADICTS`, `UNRELATED`, `INSUFFICIENT_ACCESS`, `NOT_ASSESSED`) con pasajes y limitaciones. Separa resultado automático de decisión humana; no edita el texto. |
| Proponer reemplazo/ajuste de cita | Evaluación previa, fuente candidata y pasaje localizable; cambio propuesto. | Produce diff pendiente. Solo una aceptación explícita crea nueva revisión/ocurrencia de cita; conserva el antes/después. |
| Invitar apoyo puntual | Proyecto, tarea, recursos, capacidades mínimas, vencimiento y actor invitante. | El invitado acepta antes de acceder; autorización se comprueba por recurso/job/descarga; revocación impide acceso futuro; eventos históricos permanecen. |
| Enviar respuesta de apoyo | Invitación válida, tarea, comentario/ancla y recursos consultados. | Respuesta queda ligada a tarea y versión; requiere revisión del tesista/asesor para incorporarse al documento. |
| Solicitar tarea de IA/agentes | Tipo de tarea, contexto/versiones, fuentes disponibles, proveedor/modelo permitido y actor. | Job cancelable/observable; resultados tipados y ligados a entradas; propuesta no altera contenido canónico sin aceptación. |
| Comentar/enviar/decidir capítulo | ID de snapshot/revisión, ancla, texto/decisión, expected version. | Comentario asociado a revisión exacta; ancla válida; asesor no aprueba otra versión ni snapshot con observaciones abiertas según regla vigente. |
| Calcular tabla/figura | Datos de entrada, transformación/spec, fuente/unidades y versiones. | Reproducible; resultado muestra procedencia; cambios producen versión nueva; IA no inventa cifras. |
| Exportar | Revisión/snapshot, estilo, formato y plantilla declarada. | Archivo identifica la versión; no se presenta como final institucional si faltan requisitos; referencias y campos vivos tienen verificaciones separadas. |

### Generación IA desde backend (ciclo y adaptador Gemini B5.1 implementados)

El código implementa el caso de uso del servidor (`backend/thesis/services/ai_jobs.py`): autoriza al tesista titular, resuelve dependencias y contexto del proyecto, fija prompt/workflow/contrato y versión de estado, crea un job observable `AIGenerationJob`, valida estrictamente su salida y deja una propuesta pendiente de aceptación humana (`PENDING_ACCEPTANCE`). La fábrica de proveedor está deshabilitada por defecto; el mock solo se permite en `DEBUG` y el adaptador Gemini usa `gemini-3.8-flash` por configuración de servidor. No se verificó una llamada real por falta de credenciales disponibles. Ver [especificación de generación IA y resultados](./especificacion_generacion_ia_y_resultados.md).

La salida P01–P32 pasa por `CONTRACTS`; al aceptarla se incorpora mediante `save_step`. Las tareas `USR_...` validan `output_schema` JSON Schema, separado de `parameters_schema`, y se incorporan como ejecución estructurada, no como capítulo. Aceptar revalida permiso, clave de decisión y versión del contexto; la aceptación solo usa la salida guardada y validada del job. Rechazar no escribe `StepProgress`, manuscrito ni exportación. La aprobación posterior del asesor es independiente.

No extender `DocumentJob` por conveniencia: su modelo exige destino documental único y tiene enums/constraints/recovery específicos. El job IA separado ya existe; no crear otro. Nunca exponer keys del proveedor en cliente, DB de prompts, logs o respuestas. No enviar documentos privados/PII por defecto ni afirmar retención del proveedor sin evidencia contractual.

## Reglas académicas y evidencia

- Los límites específicos actuales (cantidad de temas, longitud del título, rango de años, tamaño de matriz, número de referencias, coeficiente de piloto, etc.) se auditan y clasifican como norma confirmada, preferencia del profesor, default de plantilla o legado. No generalizarlos por estar codificados.
- IEEE es el estilo acordado como objetivo del piloto, sujeto a verificar la guía aplicable. Conservar APA legado si hay datos guardados; no mezclar estilos dentro de un mismo artefacto.
- Todo antecedente declara nivel inspeccionado: metadatos, resumen, texto extraído o lectura/verificación humana. Afirmaciones sobre metodología/resultados exigen texto completo, localizador físico y cita literal para que un humano lo compruebe.
- El sistema separa “texto extraído”, “pasaje encontrado”, “cita comprobada literalmente” y “respaldo semántico confirmado”. Una etapa técnica no certifica la siguiente.
- La revisión de una ocurrencia bibliográfica separa identidad/metadatos de relación semántica afirmación–fuente. El estado `INSUFFICIENT_ACCESS` no debe degradarse a respaldo porque exista DOI, resumen o similitud vectorial.
- Toda fuente candidata sugerida debe declarar por qué parece relacionada y el nivel de inspección. Solo un pasaje localizable permite proponerla como posible respaldo; título/resumen/similitud solo permiten proponerla como lectura candidata.
- Las búsquedas exploratorias admiten variantes amplias; una estrategia formal registra base, ecuación, filtros, fecha y criterios. La ruta Scopus/WoS manual asistida no depende de API y no atribuye al proveedor resultados de otra fuente.
- Un experto o bibliotecario invitado aporta comentarios a una tarea y recursos autorizados; el tesista decide incorporarlos y el asesor conserva las decisiones de aprobación.
- La automatización de tareas repetitivas es meta del producto. Ahorro de tiempo/errores es una hipótesis hasta ser medido con tareas comparables; no hardcodear beneficios cuantificados.
- Capítulos 1–7 pueden redactarse y estructurarse en borrador; datos de campo y resultados empíricos no disponibles permanecen pendientes, nunca fabricados.

## Multiagentes y ejecución paralela

Capacidades posibles: ideación/viabilidad, búsqueda abierta y preparación de consultas manuales por proveedor/región, deduplicación, extracción, resolución de acceso, preguntas sobre corpus, auditoría de afirmaciones y citas, búsqueda de contraevidencia, síntesis, mapeo teórico, matriz metodológica, revisión de instrumentos, adaptación del estilo propio, tratamiento de observaciones y visualización. La orquestación registra entradas, versiones, pasajes, tareas hijas, resultados, errores y aceptación. Los subagentes no se convierten en nuevos roles institucionales, no presentan una búsqueda manual como ejecución automatizada y no pueden aprobar ni cambiar el manuscrito.

El flujo detallado, las categorías de estado, tareas de apoyos invitados y criterios de aceptación están en [Especificación de búsqueda, lectura documental y revisión de afirmaciones](./especificacion_busqueda_y_revision_de_evidencia.md).
