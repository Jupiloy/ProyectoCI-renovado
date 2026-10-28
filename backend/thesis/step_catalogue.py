"""Catálogo metodológico compartido por el backend y el servidor MCP."""

from typing import Any

CATALOGO_PASOS: dict[str, dict[str, Any]] = {
    # Capítulo 1: Selección del Tema y Alcance
    "P01": {
        "capitulo": 1,
        "nombre": "Mapa de temas viables",
        "objetivo": "Generar 10 temas potenciales según intereses y área, con matriz de pros y contras.",
        "entradas_requeridas": ["carrera", "intereses", "area_investigacion"]
    },
    "P02": {
        "capitulo": 1,
        "nombre": "Matriz de factibilidad",
        "objetivo": "Comparar 3 temas preseleccionados evaluando puntajes de 1 al 5 en acceso a datos, relevancia y brecha.",
        "entradas_requeridas": ["temas_candidatos"]
    },
    "P03": {
        "capitulo": 1,
        "nombre": "Alineación ODS y relevancia",
        "objetivo": "Alinear el tema seleccionado con tendencias científicas y los Objetivos de Desarrollo Sostenible (ODS).",
        "entradas_requeridas": ["tema_seleccionado"]
    },
    "P04": {
        "capitulo": 1,
        "nombre": "Delimitación final y título",
        "objetivo": "Formular el título oficial de máximo 20 palabras (Variables + Unidad de análisis + Lugar + Tiempo).",
        "entradas_requeridas": ["tema", "unidad_analisis", "lugar", "periodo"]
    },
    "P05": {
        "capitulo": 1,
        "nombre": "Redacción de la Introducción",
        "objetivo": "Redactar el Capítulo I completo en prosa continua académica.",
        "entradas_requeridas": ["titulo", "delimitacion_confirmada"]
    },
    # Capítulo 2: Problema y Justificación
    "P06": {
        "capitulo": 2,
        "nombre": "Árbol del problema y formulación",
        "objetivo": "Construir causas/efectos y redactar la pregunta general y preguntas específicas.",
        "entradas_requeridas": ["titulo", "unidad_analisis"]
    },
    "P07": {
        "capitulo": 2,
        "nombre": "Justificación de la investigación",
        "objetivo": "Argumentar la relevancia teórica, práctica, metodológica y social del estudio.",
        "entradas_requeridas": ["problema_central"]
    },
    "P08": {
        "capitulo": 2,
        "nombre": "Originalidad y aporte",
        "objetivo": "Explicar la contribución novedosa de la tesis frente a la literatura previa.",
        "entradas_requeridas": ["brecha_detectada", "aporte_propuesto"]
    },
    # Capítulo 3: Objetivos, Preguntas e Hipótesis
    "P09": {
        "capitulo": 3,
        "nombre": "Objetivos de investigación (SMART)",
        "objetivo": "Formular objetivo general y específicos usando verbos de la Taxonomía de Bloom.",
        "entradas_requeridas": ["problema_central", "preguntas_especificas"]
    },
    "P10": {
        "capitulo": 3,
        "nombre": "Preguntas de investigación alineadas",
        "objetivo": "Verificar correspondencia biunívoca entre preguntas y objetivos con formato ¿?",
        "entradas_requeridas": ["objetivo_general", "objetivos_especificos"]
    },
    "P11": {
        "capitulo": 3,
        "nombre": "Hipótesis y variables",
        "objetivo": "Formular hipótesis general y específicas identificando variable independiente y dependiente.",
        "entradas_requeridas": ["tipo_investigacion", "preguntas", "objetivos"]
    },
    "P12": {
        "capitulo": 3,
        "nombre": "Matriz de operacionalización",
        "objetivo": "Construir matriz de variables, definiciones, dimensiones, indicadores y escala de medición.",
        "entradas_requeridas": ["variables_confirmadas"]
    },
    # Capítulo 4: Revisión de Literatura (Antecedentes)
    "P13": {
        "capitulo": 4,
        "nombre": "Ecuaciones de búsqueda académica",
        "objetivo": "Diseñar ecuaciones booleanas (AND, OR, NOT) para Scopus e IEEE Xplore.",
        "entradas_requeridas": ["variables", "palabras_clave"]
    },
    "P14": {
        "capitulo": 4,
        "nombre": "Criterios de inclusión y exclusión",
        "objetivo": "Delimitar rango temporal (últimos 5 años), tipología documental e idiomas.",
        "entradas_requeridas": ["tema_delimitado"]
    },
    "P15": {
        "capitulo": 4,
        "nombre": "Protocolo de cribado PRISMA",
        "objetivo": "Estructurar el flujograma PRISMA con métricas de identificación a inclusión.",
        "entradas_requeridas": ["registros_identificados"]
    },
    "P16": {
        "capitulo": 4,
        "nombre": "Matriz de literatura científica",
        "objetivo": "Sintetizar antecedentes con autores, año, metodología, muestra y hallazgos.",
        "entradas_requeridas": ["articulos_incluidos"]
    },
    "P17": {
        "capitulo": 4,
        "nombre": "Síntesis temática y patrones",
        "objetivo": "Identificar convergencias, divergencias y patrones metodológicos en la literatura.",
        "entradas_requeridas": ["matriz_literatura"]
    },
    "P18": {
        "capitulo": 4,
        "nombre": "Brecha y agenda de investigación",
        "objetivo": "Argumentar con rigor empírico el vacío que la tesis resuelve.",
        "entradas_requeridas": ["sintesis_tematica"]
    },
    "P19": {
        "capitulo": 4,
        "nombre": "Redacción del marco de antecedentes",
        "objetivo": "Redactar antecedentes internacionales y nacionales en prosa académica estructurada.",
        "entradas_requeridas": ["estudios_seleccionados"]
    },
    "P20": {
        "capitulo": 4,
        "nombre": "Citas y referencias normalizadas",
        "objetivo": "Formatear referencias bibliográficas según normativa IEEE o APA 7ª edición.",
        "entradas_requeridas": ["fuentes_citadas", "estilo_citacion"]
    },
    # Capítulo 5: Marco Teórico y Conceptual
    "P21": {
        "capitulo": 5,
        "nombre": "Selección de teorías base",
        "objetivo": "Fundamentar el estudio en marcos teóricos y postulados científicos consolidados.",
        "entradas_requeridas": ["variables", "area_disciplinar"]
    },
    "P22": {
        "capitulo": 5,
        "nombre": "Definiciones y constructos",
        "objetivo": "Definir constructos clave con autores clásicos y contemporáneos.",
        "entradas_requeridas": ["variables", "teorias"]
    },
    "P23": {
        "capitulo": 5,
        "nombre": "Modelo conceptual y relacional",
        "objetivo": "Representar la interacción entre variables mediante modelo conceptual y diagrama Mermaid.",
        "entradas_requeridas": ["variables", "definiciones"]
    },
    "P24": {
        "capitulo": 5,
        "nombre": "Proposiciones derivadas",
        "objetivo": "Deducir argumentos teóricos que sustentan las hipótesis.",
        "entradas_requeridas": ["modelo_conceptual", "hipotesis"]
    },
    # Capítulo 6: Metodología
    "P25": {
        "capitulo": 6,
        "nombre": "Enfoque y diseño metodológico",
        "objetivo": "Clasificar enfoque, diseño, nivel de alcance y corte temporal del estudio.",
        "entradas_requeridas": ["problema", "objetivos", "hipotesis"]
    },
    "P26": {
        "capitulo": 6,
        "nombre": "Técnicas e instrumentos previstos",
        "objetivo": "Justificar técnicas de recolección y procedimientos de campo.",
        "entradas_requeridas": ["variables", "indicadores"]
    },
    "P27": {
        "capitulo": 6,
        "nombre": "Validez y confiabilidad",
        "objetivo": "Establecer métodos de validación de expertos (V de Aiken) y consistencia interna (Alfa / Omega).",
        "entradas_requeridas": ["instrumentos"]
    },
    "P28": {
        "capitulo": 6,
        "nombre": "Aspectos éticos y consentimiento",
        "objetivo": "Definir consentimiento informado, confidencialidad y principios éticos universitarios.",
        "entradas_requeridas": ["poblacion", "datos"]
    },
    "P29": {
        "capitulo": 6,
        "nombre": "Redacción del capítulo metodológico",
        "objetivo": "Redactar el capítulo completo de metodología según formato institucional.",
        "entradas_requeridas": ["diseno", "procedimientos", "etica"]
    },
    # Capítulo 7: Instrumentos de Recolección de Datos
    "P30": {
        "capitulo": 7,
        "nombre": "Cuestionario cuantitativo",
        "objetivo": "Elaborar banco de ítems por dimensión en escala Likert.",
        "entradas_requeridas": ["matriz_operacionalizacion"]
    },
    "P31": {
        "capitulo": 7,
        "nombre": "Guía de entrevista en profundidad",
        "objetivo": "Diseñar guía de preguntas abiertas y repreguntas para informantes clave.",
        "entradas_requeridas": ["variables", "objetivos_cualitativos"]
    },
    "P32": {
        "capitulo": 7,
        "nombre": "Prueba piloto y calibración",
        "objetivo": "Documentar muestra piloto, coeficiente de confiabilidad y ajustes a los reactivos.",
        "entradas_requeridas": ["instrumento_preliminar"]
    }
}

