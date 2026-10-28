# Ficha Técnica y Planteamiento Formal del Proyecto

> **Estado verificado al 18/10/2026:** el producto implementa P01–P32, MCP/API, panel del asesor y evidencia documental. No se ha validado todavía con usuarios reales ni se ha desplegado públicamente.

## 1. Título del Proyecto
**"Desarrollo de una Plataforma Colaborativa basada en Protocolo MCP, Roles Secuenciales y Validación Determinista para la Asistencia Metodológica y Supervisión de Tesis Universitarias"**

---

## 2. Planteamiento de la Problemática

### 2.1 Contexto
La formulación de investigaciones académicas y tesis conducentes a grados y títulos universitarios exige el cumplimiento de una secuencia metodológica rigurosa, estandarizada e interdependiente. Tradicionalmente, este proceso abarca desde la exploración del tema, formulación del problema y matriz de consistencia, hasta el marco teórico y diseño de instrumentos de medición.

### 2.2 Problema Central
Aunque existen secuencias estructuradas de *prompts* para asistir esta labor mediante Modelos de Lenguaje (LLMs), su utilización en interfaces de chat tradicionales presenta tres fallas críticas de ingeniería y metodología:

1. **Pérdida de Continuidad y Ruptura de Memoria:** Los chats comerciales carecen de un motor de persistencia del estado metodológico. El usuario debe copiar y pegar manualmente variables (variable independiente, dependiente, unidad de análisis, contexto geográfico y temporal) a lo largo de más de 30 etapas, provocando alucinaciones, inconsistencias entre objetivos y preguntas, y olvido de restricciones.
2. **Desconexión y Sobrecarga del Asesor:** No existe un canal integrado para que el docente/asesor supervise en tiempo real el progreso de múltiples tesistas, obligando al uso de correos electrónicos y versiones desordenadas de archivos Word sin trazabilidad de decisiones.
3. **Alucinación Bibliográfica y Riesgo Ético:** Los buscadores generales de IA inventan citas bibliográficas, autores y DOIs ficticios al no estar conectados a bases de datos científicas formales. Además, sin límites claros, las IAs pueden simular datos de campo empíricos, atentando contra la ética de la investigación.

---

## 3. Objetivos del Proyecto

### 3.1 Objetivo General
Desarrollar una plataforma integral sustentada en el protocolo **MCP (Model Context Protocol)** y roles secuenciales del cliente LLM y validación determinista en el backend que apoyen la ejecución secuencial y asistida de los capítulos 1 al 7 de una tesis, fundamentándose en fuentes reales del tesista y facilitando la supervisión colaborativa asíncrona por parte del asesor.

### 3.2 Objetivos Específicos
* **OE1 (Diseño Metodológico y Persistencia):** Modelar los pasos `P01` a `P32` y un esquema relacional por proyecto: `research_profile` para contexto y versión, `consistency_row` para preguntas, objetivos e hipótesis, `step_progress` para el avance y `chapter_revision` para el texto histórico. El [diccionario físico](../02_arquitectura_y_sistema/modelo_datos_fisico.md) define las demás entidades y sus relaciones.
* **OE2 (Servidor MCP y Conectividad):** Implementar el servidor MCP con herramientas especializadas para la inyección de plantillas, gestión de estados y vinculación con clientes de IA (Claude Desktop, Cursor o Web).
* **OE3 (Búsqueda y evidencia):** Integrar OpenAlex, Semantic Scholar y la API REST de ALICIA/CONCYTEC. Sus resultados se tratan como metadatos hasta incorporar y extraer un PDF.
* **OE4 (Capa determinista):** Aplicar contratos, reglas de dominio, conteo físico de páginas, hashes y citas localizadas sin que el backend llame a un LLM. Estas comprobaciones reducen clases concretas de error, pero no garantizan ausencia total de alucinaciones ni verdad científica.
* **OE5 (Asesor y Word):** Proveer Django Admin/Unfold y API para observaciones y decisiones sobre revisiones inmutables, además de un borrador DOCX editable. La carátula institucional completa y el reporte de similitud siguen pendientes.

---

## 4. Alcance y Límites Éticos

* **Alcance Metodológico Válido:** Abarca rigurosamente desde el **Capítulo 1 (Selección del tema y alcance)** hasta el **Capítulo 7 (Diseño de instrumentos: cuestionarios y entrevistas)**.
* **Barrera ética:** El alcance termina en el diseño de instrumentos. El sistema no implementa capítulos de resultados ni genera respuestas de encuesta. P32 todavía recibe un coeficiente declarado por el cliente; por ello la procedencia empírica debe comprobarse con datos crudos y revisión humana.
