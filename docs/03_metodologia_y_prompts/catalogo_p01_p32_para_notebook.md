# Catálogo P01–P32 del backend para análisis en Notebook

> Copia fiel de `CATALOGO_PASOS` en `backend/thesis/step_catalogue.py`. No es una norma UTP ni el paquete original de 50 prompts. Los objetivos y entradas reflejan el código actual; no implican que el orden o contenido metodológico sean definitivos.
> SHA-256 del archivo fuente: `b4ae5e956763e2ea4bf8a2b23bea5c6519085bb75602c79b2f9a395ab86d025a`.

| Código | Capítulo interno | Nombre | Objetivo literal del catálogo | Entradas requeridas literales |
| :--- | :---: | :--- | :--- | :--- |
| P01 | 1 | Mapa de temas viables | Generar 10 temas potenciales según intereses y área, con matriz de pros y contras. | `carrera`, `intereses`, `area_investigacion` |
| P02 | 1 | Matriz de factibilidad | Comparar 3 temas preseleccionados evaluando puntajes de 1 al 5 en acceso a datos, relevancia y brecha. | `temas_candidatos` |
| P03 | 1 | Alineación ODS y relevancia | Alinear el tema seleccionado con tendencias científicas y los Objetivos de Desarrollo Sostenible (ODS). | `tema_seleccionado` |
| P04 | 1 | Delimitación final y título | Formular el título oficial de máximo 20 palabras (Variables + Unidad de análisis + Lugar + Tiempo). | `tema`, `unidad_analisis`, `lugar`, `periodo` |
| P05 | 1 | Redacción de la Introducción | Redactar el Capítulo I completo en prosa continua académica. | `titulo`, `delimitacion_confirmada` |
| P06 | 2 | Árbol del problema y formulación | Construir causas/efectos y redactar la pregunta general y preguntas específicas. | `titulo`, `unidad_analisis` |
| P07 | 2 | Justificación de la investigación | Argumentar la relevancia teórica, práctica, metodológica y social del estudio. | `problema_central` |
| P08 | 2 | Originalidad y aporte | Explicar la contribución novedosa de la tesis frente a la literatura previa. | `brecha_detectada`, `aporte_propuesto` |
| P09 | 3 | Objetivos de investigación (SMART) | Formular objetivo general y específicos usando verbos de la Taxonomía de Bloom. | `problema_central`, `preguntas_especificas` |
| P10 | 3 | Preguntas de investigación alineadas | Verificar correspondencia biunívoca entre preguntas y objetivos con formato ¿? | `objetivo_general`, `objetivos_especificos` |
| P11 | 3 | Hipótesis y variables | Formular hipótesis general y específicas identificando variable independiente y dependiente. | `tipo_investigacion`, `preguntas`, `objetivos` |
| P12 | 3 | Matriz de operacionalización | Construir matriz de variables, definiciones, dimensiones, indicadores y escala de medición. | `variables_confirmadas` |
| P13 | 4 | Ecuaciones de búsqueda académica | Diseñar ecuaciones booleanas (AND, OR, NOT) para Scopus e IEEE Xplore. | `variables`, `palabras_clave` |
| P14 | 4 | Criterios de inclusión y exclusión | Delimitar rango temporal (últimos 5 años), tipología documental e idiomas. | `tema_delimitado` |
| P15 | 4 | Protocolo de cribado PRISMA | Estructurar el flujograma PRISMA con métricas de identificación a inclusión. | `registros_identificados` |
| P16 | 4 | Matriz de literatura científica | Sintetizar antecedentes con autores, año, metodología, muestra y hallazgos. | `articulos_incluidos` |
| P17 | 4 | Síntesis temática y patrones | Identificar convergencias, divergencias y patrones metodológicos en la literatura. | `matriz_literatura` |
| P18 | 4 | Brecha y agenda de investigación | Argumentar con rigor empírico el vacío que la tesis resuelve. | `sintesis_tematica` |
| P19 | 4 | Redacción del marco de antecedentes | Redactar antecedentes internacionales y nacionales en prosa académica estructurada. | `estudios_seleccionados` |
| P20 | 4 | Citas y referencias normalizadas | Formatear referencias bibliográficas según normativa IEEE o APA 7ª edición. | `fuentes_citadas`, `estilo_citacion` |
| P21 | 5 | Selección de teorías base | Fundamentar el estudio en marcos teóricos y postulados científicos consolidados. | `variables`, `area_disciplinar` |
| P22 | 5 | Definiciones y constructos | Definir constructos clave con autores clásicos y contemporáneos. | `variables`, `teorias` |
| P23 | 5 | Modelo conceptual y relacional | Representar la interacción entre variables mediante modelo conceptual y diagrama Mermaid. | `variables`, `definiciones` |
| P24 | 5 | Proposiciones derivadas | Deducir argumentos teóricos que sustentan las hipótesis. | `modelo_conceptual`, `hipotesis` |
| P25 | 6 | Enfoque y diseño metodológico | Clasificar enfoque, diseño, nivel de alcance y corte temporal del estudio. | `problema`, `objetivos`, `hipotesis` |
| P26 | 6 | Técnicas e instrumentos previstos | Justificar técnicas de recolección y procedimientos de campo. | `variables`, `indicadores` |
| P27 | 6 | Validez y confiabilidad | Establecer métodos de validación de expertos (V de Aiken) y consistencia interna (Alfa / Omega). | `instrumentos` |
| P28 | 6 | Aspectos éticos y consentimiento | Definir consentimiento informado, confidencialidad y principios éticos universitarios. | `poblacion`, `datos` |
| P29 | 6 | Redacción del capítulo metodológico | Redactar el capítulo completo de metodología según formato institucional. | `diseno`, `procedimientos`, `etica` |
| P30 | 7 | Cuestionario cuantitativo | Elaborar banco de ítems por dimensión en escala Likert. | `matriz_operacionalizacion` |
| P31 | 7 | Guía de entrevista en profundidad | Diseñar guía de preguntas abiertas y repreguntas para informantes clave. | `variables`, `objetivos_cualitativos` |
| P32 | 7 | Prueba piloto y calibración | Documentar muestra piloto, coeficiente de confiabilidad y ajustes a los reactivos. | `instrumento_preliminar` |
