# Análisis neutral de la demostración del producto esperado

- **Fecha del audio:** 2026-10-22, según los nombres de los audios entregados por el usuario.
- **Fuente textual inspeccionada íntegramente:** `transcripci_n_de_la_reuni_n.md`.
- **Huella SHA-256 de la fuente:** `5144634bd18b5726f04edb2953395bf2fb706ce433f0615c64f7408164ee195c`.
- **Cobertura temporal de la transcripción:** 00:00–14:10.
- **Nivel de verificación:** análisis del texto completo de una transcripción automática; no se verificó esta transcripción contra el audio ni la aplicación mostrada en pantalla.
- **Identificación de hablantes:** no existe diarización. Las funciones mostradas por un hablante se registran como afirmaciones y demostraciones, no como capacidades técnicamente comprobadas.
- **Estado:** analizada; requiere verificación técnica independiente de la herramienta exhibida.

## 1. Conclusión neutral

Esta reunión muestra el tipo de experiencia final que un usuario académico consideraría valiosa: estructura de documento, formato institucional, citas vinculadas, antecedentes relacionados con la investigación, figuras y tablas explicadas y descarga a Word. También contiene dos valoraciones explícitas favorables: “el proyecto está bien” (10:45) y “el proyecto está... está bien ejecutado” (14:10), acompañadas por la recomendación de “explotarlo un poquito más” y encaminarlo mejor.

Eso no equivale a una decisión de reemplazar TesisMCP por un generador autónomo de tesis. La demostración funciona como referencia de expectativas de usuario. Además, las capacidades de la herramienta mostrada —incluidas sus supuestas conexiones— no fueron inspeccionadas técnicamente y no deben asumirse como verdaderas solo por la conversación.

## 2. Registro de evidencia clasificada

| Tiempo | Tipo de intervención | Evidencia o paráfrasis fiel | Certeza | Implicación posible para TesisMCP |
| :---: | :--- | :--- | :---: | :--- |
| 00:00–00:35 | Demostración | Se muestra estructura, índice de contenido, índice de tablas y referencias cruzadas. | Alta respecto de la narración; no verificada en software | La salida esperada se aproxima a un documento académico editable y estructurado. |
| 00:40–01:30 | Demostración | Las citas visibles se atribuyen a enlaces con Zotero o Mendeley, a diferencia del texto plano de un chat. | Media | Evaluar campos de cita activos y sincronización; no asumir que la herramienta realmente consulta repositorios. |
| 01:30–02:13 | Requisito propuesto | Formato tipográfico y estilos de citación ajustables; se mencionan APA, IEEE y Vancouver. | Alta respecto de lo dicho | Parametrizar formato por guía institucional en una etapa futura. |
| 02:25–02:45 | Requisito propuesto | Cada tabla debería incluir número, título, nota y fuente. | Alta | Añadir validaciones estructurales del documento. |
| 03:15–03:40 | Consejo y riesgo | Separar dimensiones de justificación y no permitir que el chat redacte “cualquier cosa”. | Alta | Usar contratos metodológicos y estructura explícita. |
| 04:00–04:20 | Pregunta técnica | Se pregunta si la herramienta usa LaTeX; el hablante responde que no sabe cómo funciona internamente. | Alta | LaTeX no queda confirmado como requisito ni como implementación. |
| 04:30–05:30 | Demostración | Se afirma que los antecedentes se descargan de Scopus, se clasifican geográficamente y se relacionan con variables del estudio. | Media; afirmación no verificada | La relación entre fuente y tesis sí es una necesidad; la conexión técnica debe comprobarse. |
| 06:55–08:45 | Requisito propuesto | El producto debe redactar metodológicamente, relacionar tablas/figuras con el marco teórico y mantener referencias vinculadas. | Alta respecto de la expectativa | Reforzar estructura, procedencia y correspondencia entre afirmaciones y fuentes. |
| 09:00–09:30 | Hipótesis técnica | Se especula que la herramienta usa LaTeX; luego se describe una interfaz propia. | Baja para LaTeX | No tomar la especulación como decisión arquitectónica. |
| 10:15–10:45 | Necesidad del usuario | Cada universidad tiene su estructura; el usuario “del otro lado” necesitaría una salida como la mostrada. | Alta | Separar un núcleo metodológico de plantillas institucionales. |
| 10:45–11:30 | Evaluación y recomendación | “El proyecto está bien”, pero debe explotarse y encaminarse mejor; se recomienda hacerlo ahora con el modelo UTP. | Alta | Mantener la idea y reducir el primer alcance al caso UTP. |
| 11:50–12:20 | Idea técnica | Se discute evitar que Scopus detecte automatización y se menciona código obtenido de GitHub sin comprenderlo completamente. | Alta respecto de la conversación | No implementar evasión de controles ni reutilizar código sin auditoría y licencia. |
| 12:30–12:35 | Riesgo de seguridad | Se reconoce que descargar archivos desconocidos de GitHub puede introducir software malicioso. | Alta | Auditar dependencias, procedencia y licencias. |
| 13:35–14:10 | Evaluación final | Se pide mejorar el proyecto, especialmente la interfaz; se reitera que está bien ejecutado y que podría orientarse a ferias. | Alta | La ampliación es aspiracional; debe separarse del alcance académico inmediato. |

## 3. Clasificación temática

### Necesidades de experiencia de usuario

- Visualizar una estructura de tesis comprensible.
- Obtener un borrador Word editable con tablas, figuras y referencias organizadas.
- Reconocer de dónde provienen las citas y cómo se relacionan con el estudio.
- Adaptar la presentación a la institución y carrera.
- Recibir redacción metodológica estructurada, no texto genérico.

### Consejos y observaciones

- Comenzar con la estructura UTP.
- Cuidar los detalles que un asesor revisa: título, numeración, notas, fuentes y relaciones metodológicas.
- Mejorar la interfaz y la comunicación del flujo.
- Separar el problema funcional de la tecnología interna usada para resolverlo.

### Riesgos y limitaciones

- La herramienta presentada no fue auditada; sus conexiones con Scopus, Zotero, Mendeley o LaTeX no están demostradas.
- Automatizar acceso a servicios de terceros puede incumplir condiciones de uso o controles técnicos.
- Copiar repositorios sin entenderlos introduce riesgos de seguridad, licencia y mantenimiento.
- Producir un Word visualmente correcto no demuestra validez científica.

### Ideas futuras, no decisiones

- Compatibilidad con múltiples estilos y universidades.
- Campos de citas activos para Zotero/Mendeley.
- Conexión directa con Scopus.
- Uso interno de LaTeX.
- Preparación del producto para ferias.

## 4. Decisiones que no quedaron demostradas

- No se acordó imitar exactamente la herramienta mostrada.
- No se confirmó que LaTeX sea necesario.
- No se autorizó automatizar Scopus ni evadir sus controles.
- No se definió una integración real de Zotero/Mendeley.
- No se cambió formalmente el alcance de Integrador 1.

## 5. Preguntas de seguimiento

1. ¿Qué elementos del Word son obligatorios para el piloto UTP y cuáles pueden esperar?
2. ¿Se requieren citas activas o basta inicialmente con referencias trazables y verificadas?
3. ¿La interfaz del tesista forma parte de la entrega vigente o solo de una visión futura?
4. ¿Qué funciones de la demostración pueden comprobarse con documentación o acceso técnico?

