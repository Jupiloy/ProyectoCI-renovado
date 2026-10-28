# Estructura de Capítulos y Mapeo de Prompts (1 al 7)

> **Estado del catálogo existente:** este documento describe la secuencia P01–P32 implementada, no el orden metodológico objetivo. La [propuesta de orden revisado](./propuesta_orden_metodologico_revisado.md) separa rutas por enfoque, reordena dependencias y plantea asistencia sobre datos empíricos reales más allá de P32. Hasta que se apruebe e implemente, los contratos y servicios actuales siguen siendo la fuente de verdad ejecutable.

Este documento detalla 32 pasos metodológicos con identificadores únicos (`P01` a `P32`) extraídos del material de referencia (*@SilverLawyer* / Asesor), correspondientes a las fases válidas y éticas de asistencia con Inteligencia Artificial.

---

## Capítulo 1 · Selección del Tema y Alcance
* **Objetivo:** Definir un tema viable, delimitado en tiempo, espacio y población, vinculado a un ODS y a la guía universitaria.
* **Prompts incluidos:**
  * `Prompt #1`: **Mapa de temas viables.** Genera 10 temas potenciales según intereses y área, con matriz de pros y contras.
  * `Prompt #2`: **Matriz de factibilidad.** Compara 3 temas preseleccionados evaluando puntajes del 1 al 5 en acceso a datos, relevancia y brecha.
  * `Prompt #3`: **Análisis de temas más relevantes a 2026.** Alinea el tema con tendencias y los Objetivos de Desarrollo Sostenible (ODS).
  * `Prompt #4`: **Delimitación final del tema.** Formula el título oficial de máximo 20 palabras: Variable(s) + Unidad de análisis + Lugar + Tiempo.
  * `Prompt #5`: **Redacción de la Introducción definitiva.** Redacta el Capítulo I completo en prosa continua académica.

---

## Capítulo 2 · Problema y Justificación
* **Objetivo:** Identificar las causas y efectos del problema central y justificar su relevancia.
* **Prompts incluidos:**
  * `Prompt #6`: **Árbol y formulación del problema.** Construye las causas y consecuencias y redacta la pregunta general y específicas de forma investigable.
  * `Prompt #7`: **Justificación de la investigación.** Argumenta la relevancia teórica, práctica, metodológica y social.
  * `Prompt #8`: **Originalidad y aporte del estudio.** Explica la contribución novedosa de la tesis frente a la literatura previa.

---

## Capítulo 3 · Objetivos, Preguntas e Hipótesis
* **Objetivo:** Convertir el problema en metas alcanzables y estructurar la matriz de consistencia.
* **Prompts incluidos:**
  * `Prompt #9`: **Objetivos generales y específicos (SMART).** Define metas medibles con verbos en infinitivo (Taxonomía de Bloom).
  * `Prompt #10`: **Preguntas de investigación.** Verifica correspondencia biunívoca entre preguntas y objetivos.
  * `Prompt #11`: **Hipótesis y variables.** Formula hipótesis general y específicas; identifica variables dependientes e independientes.
  * `Prompt #12`: **Tabla de operacionalización.** Construye la matriz de variables, dimensiones, indicadores y escalas de medición.

---

## Capítulo 4 · Revisión de Literatura (Antecedentes)
* **Objetivo:** Mapear el estado del arte y construir el marco de antecedentes con evidencia real.
* **Prompts incluidos:**
  * `Prompt #13`: **Ecuaciones de búsqueda.** Diseña cadenas booleanas (`AND`, `OR`, `NOT`) para Scopus, IEEE Xplore y WoS.
  * `Prompt #14`: **Criterios de inclusión y exclusión.** Delimita años (últimos 5 años), tipo de documento e idioma.
  * `Prompt #15`: **Protocolo tipo PRISMA.** Flujograma de identificación, cribado, elegibilidad e inclusión de estudios.
  * `Prompt #16`: **Matriz de literatura.** Tabla comparativa de autores, metodologías, muestras y resultados clave.
  * `Prompt #17`: **Síntesis temática.** Identifica patrones y consensos en los hallazgos de los autores.
  * `Prompt #18`: **Brecha y agenda de investigación.** Argumenta el vacío que la tesis viene a resolver.
  * `Prompt #19`: **Redacción del marco de antecedentes.** Estructura formal de párrafos de antecedentes nacionales e internacionales.
  * `Prompt #20`: **Citas y referencias bibliográficas.** El piloto prioriza **IEEE** y conserva `APA_7` para compatibilidad histórica; el contrato admite ambos. El formato de cada entrada requiere revisión humana.

---

## Capítulo 5 · Marco Teórico y Conceptual
* **Objetivo:** Fundamentar el estudio en teorías científicas consolidadas.
* **Prompts incluidos:**
  * `Prompt #21`: **Selección de teorías.** Escoge 2 o 3 marcos teóricos de referencia.
  * `Prompt #22`: **Definiciones y constructos.** Define formalmente los conceptos clave con autores clásicos y contemporáneos.
  * `Prompt #23`: **Modelo conceptual.** Representación lógica o diagrama de la relación entre variables.
  * `Prompt #24`: **Proposiciones derivadas.** Deduce argumentos que sustentan las hipótesis planteadas.

---

## Capítulo 6 · Metodología
* **Objetivo:** Describir la ruta técnica, diseño y procedimientos del estudio.
* **Prompts incluidos:**
  * `Prompt #25`: **Enfoque y diseño.** Clasificación (Cuantitativo/Cualitativo/Mixto, Experimental o No experimental, Transversal/Longitudinal).
  * `Prompt #26`: **Indicadores y técnicas de recolección.** Justifica el uso de encuestas, entrevistas o guías de observación.
  * `Prompt #27`: **Validez y confiabilidad.** Métodos de juicio de expertos (V de Aiken) y consistencia interna (Alfa de Cronbach / McDonald's Omega).
  * `Prompt #28`: **Ética y permisos.** Consentimiento informado, confidencialidad y principios éticos.
  * `Prompt #29`: **Redacción completa del capítulo de metodología.** Adaptado al formato institucional de la universidad.

---

## Capítulo 7 · Instrumentos de Recolección de Datos
* **Objetivo:** Diseñar las herramientas prácticas listas para aplicar en campo.
* **Prompts incluidos:**
  * `Prompt #30`: **Cuestionario cuantitativo.** Banco de ítems organizados por dimensión con escala Likert (1 a 5).
  * `Prompt #31`: **Guía de entrevista o Focus Group.** Preguntas abiertas cualitativas y preguntas de profundización.
  * `Prompt #32`: **Piloto y ajuste del instrumento.** Matriz de evaluación previa para calibrar la claridad de los reactivos.

---

## Correspondencia de los pasos con el modelo de datos

El [modelo físico](../02_arquitectura_y_sistema/modelo_datos_fisico.md) distingue los datos canónicos de la tesis, las salidas específicas de un paso y el texto redactado. `step_progress` registra el estado de `P01` a `P32`; el código actual crea una `chapter_revision` por guardado de paso con su `step_code` y Markdown entregado. Aún falta garantizar una instantánea completa del capítulo aprobado, como explica la [guía de backend completo](../02_arquitectura_y_sistema/guia_backend_version_completa_para_agentes.md). Las demás tablas dependen del contenido del paso:

| Pasos | Datos canónicos que actualizan | Fase de implementación |
| :--- | :--- | :--- |
| `P01`–`P04` | `project.title` y `research_profile` (tema, ODS y delimitación). | MVP. |
| `P05` | Revisión del capítulo 1; su salida estructurada queda en `step_progress` y, al aceptar una propuesta IA, `contenido_markdown` se conserva como texto en `chapter_revision`. | MVP. |
| `P06`–`P08` | `research_profile.problem_statement` y filas de `consistency_row` para las preguntas; el árbol y la justificación se conservan como salidas del paso y revisiones. | MVP. |
| `P09`–`P12` | Objetivos e hipótesis en `consistency_row`; variables, dimensiones e indicadores en sus tablas propias; `consistency_row_variable` enlaza filas y variables desde P11. | Implementado. |
| `P13`–`P20` | Fuentes, extractos y vínculos de evidencia en `source_document`, `source_excerpt` y `evidence_link`; criterios y síntesis en salidas estructuradas y revisiones. | Implementado; requiere revisión humana de la evidencia. |
| `P21`–`P29` | Contexto metodológico en `research_profile`, salidas estructuradas en `step_progress` y redacción en `chapter_revision`. | Implementado. |
| `P30`–`P32` | Versiones de `instrument` e `instrument_item`; `instrument_item_indicator` registra qué indicadores mide cada ítem. Los ajustes del piloto crean una versión nueva. | Implementado; P32 no recalcula el coeficiente desde datos crudos. |

El servicio valida permisos, prerrequisitos y coherencia antes de cambiar estas tablas. Los esquemas formales Pydantic v2 y los validadores deterministas de dominio (límite de 20 palabras, signos de interrogación y verbos de Bloom) están especificados en [Contratos Pydantic y Validadores Deterministas](./contratos_pydantic_y_validadores_mvp.md). El contenido generado por un cliente de IA solo se persiste después de la confirmación del tesista.

## Alcance actual y tratamiento de la evidencia empírica

El catálogo implementado termina en P32 y todavía no ofrece un flujo completo para muestreo, recolección, limpieza, análisis, resultados, discusión y conclusiones. La [propuesta de orden revisado](./propuesta_orden_metodologico_revisado.md) plantea asistencia en esas fases bajo datos auténticos, cálculo trazable y revisión humana. La plataforma no debe presentar datos, citas de participantes ni resultados simulados como hallazgos reales.

