"""Plantillas de prompts para el Capítulo 6: Metodología (P25 a P29)."""

CHAPTER_6_TEMPLATES = {
    "P25": {
        "step_code": "P25",
        "prompt_name": "paso_p25_enfoque_diseno",
        "titulo": "P25: Enfoque, Diseño y Alcance Metodológico",
        "descripcion": "Clasifica y fundamenta el enfoque (CUANTITATIVO), diseño (PREEXPERIMENTAL), alcance y corte temporal.",
        "guia_metodologica": """
Clasificación formal de la investigación:
1. enfoque: debe ser CUANTITATIVO, CUALITATIVO o MIXTO (en ingeniería comúnmente CUANTITATIVO).
2. diseno: debe ser EXPERIMENTAL, PREEXPERIMENTAL, CUASIEXPERIMENTAL o NO_EXPERIMENTAL.
3. nivel_alcance: debe ser EXPLORATORIO, DESCRIPTIVO, CORRELACIONAL o EXPLICATIVO.
4. corte_temporal: TRANSVERSAL o LONGITUDINAL.
5. justificacion_diseno: fundamentación metodológica de 30 a 600 caracteres explicando por qué se seleccionó este diseño frente a la hipótesis.
""",
        "esquema_json_ejemplo": {
            "enfoque": "CUANTITATIVO",
            "diseno": "PREEXPERIMENTAL",
            "nivel_alcance": "EXPLICATIVO",
            "corte_temporal": "TRANSVERSAL",
            "justificacion_diseno": "Se adopta un diseño preexperimental con pretest y postest en un solo grupo para evaluar la variación en los indicadores de consistencia y tiempo de revisión tras la implementación del sistema web con protocolo MCP."
        }
    },
    "P26": {
        "step_code": "P26",
        "prompt_name": "paso_p26_tecnicas_instrumentos",
        "titulo": "P26: Técnicas e Instrumentos de Recolección",
        "descripcion": "Justifica las técnicas (encuesta, análisis documental) y los instrumentos previstos de recolección.",
        "guia_metodologica": """
Técnicas e instrumentos de recolección:
1. tecnicas_seleccionadas: entre 1 y 5 técnicas (ej. ["Encuesta", "Análisis documental automatizado"]).
2. instrumentos_previstos: entre 1 y 5 instrumentos correspondientes (ej. ["Cuestionario en escala Likert", "Ficha de cotejo de consistencia"]).
3. procedimiento_recoleccion: descripción detallada de 40 a 800 caracteres del proceso paso a paso para aplicar los instrumentos.
""",
        "esquema_json_ejemplo": {
            "tecnicas_seleccionadas": [
                "Encuesta estructurada",
                "Análisis de registros de auditoría en base de datos"
            ],
            "instrumentos_previstos": [
                "Cuestionario de usabilidad y consistencia metodológica (Escala Likert)",
                "Lista de cotejo automatizada de contratos Pydantic superados"
            ],
            "procedimiento_recoleccion": "Se aplicará la lista de cotejo sobre los borradores iniciales de los tesistas (pretest). Posteriormente, se habilitará el servidor MCP para estructurar los pasos P01 a P32 y se medirán los tiempos de respuesta y errores bloqueados (postest), concluyendo con el cuestionario a estudiantes y asesores."
        }
    },
    "P27": {
        "step_code": "P27",
        "prompt_name": "paso_p27_validez_confiabilidad",
        "titulo": "P27: Validez y Confiabilidad Metodológica",
        "descripcion": "Establece los métodos de validez (Juicio de expertos V de Aiken) y confiabilidad (Alfa de Cronbach).",
        "guia_metodologica": """
Parámetros psicométricos y de rigor:
1. validez_instrumento: debe ser JUICIO_EXPERTOS_AIKEN, ANALISIS_FACTORIAL o VALIDEZ_CONTENIDO.
2. confiabilidad_metodo: debe ser ALFA_CRONBACH, OMEGA_MCDONALD, KR_20 o TEST_RETEST.
3. criterio_aceptabilidad: criterio umbral de aceptación estadística (10 a 300 caracteres, ej. 'V de Aiken >= 0.80 y Alfa de Cronbach >= 0.70').
""",
        "esquema_json_ejemplo": {
            "validez_instrumento": "JUICIO_EXPERTOS_AIKEN",
            "confiabilidad_metodo": "ALFA_CRONBACH",
            "criterio_aceptabilidad": "Se requiere un coeficiente V de Aiken superior a 0.80 evaluado por tres expertos temáticos y un coeficiente Alfa de Cronbach igual o mayor a 0.75 en la prueba piloto."
        }
    },
    "P28": {
        "step_code": "P28",
        "prompt_name": "paso_p28_etica_consentimiento",
        "titulo": "P28: Consideraciones Éticas y Consentimiento Informado",
        "descripcion": "Define el consentimiento informado, principios éticos y política de protección de datos personales.",
        "guia_metodologica": """
Integridad y ética en la investigación:
1. consentimiento_informado_requerido: valor booleano (true/false).
2. principios_eticos_aplicados: lista de 2 a 6 principios (ej. Beneficencia, Confidencialidad, Integridad científica, No maleficencia).
3. politica_confidencialidad_datos: directiva de protección de datos y anonimización de 30 a 500 caracteres (según Ley 29733 de Protección de Datos Personales en el Perú).
""",
        "esquema_json_ejemplo": {
            "consentimiento_informado_requerido": True,
            "principios_eticos_aplicados": [
                "Principio de integridad científica y combate al fraude académico",
                "Principio de confidencialidad y anonimización de datos",
                "Principio de consentimiento libre y esclarecido"
            ],
            "politica_confidencialidad_datos": "Los datos recopilados de los estudiantes y docentes se mantendrán en estricta confidencialidad bajo identificadores alfanuméricos anonimizados, utilizándose exclusivamente con fines de investigación académica institucional."
        }
    },
    "P29": {
        "step_code": "P29",
        "prompt_name": "paso_p29_redaccion_metodologia",
        "titulo": "P29: Redacción Integral del Capítulo de Metodología",
        "descripcion": "Redacta el Capítulo VI completo en prosa académica asegurando concordancia exacta de palabras totales.",
        "guia_metodologica": """
Redacción formal del Capítulo de Metodología:
1. Redacta el capítulo en prosa continua detallada en formato Markdown con al menos 200 caracteres y 100 palabras.
2. REGLA ESTRICTA DE CONTEO: El campo `palabras_totales` DEBE COINCIDIR EXACTAMENTE con `len(contenido_markdown.split())`.
3. Estructura el texto en: Enfoque y diseño, Población y muestra, Procedimiento de intervención y Plan de análisis estadístico.
""",
        "esquema_json_ejemplo": {
            "contenido_markdown": "El procedimiento de ejecución metodológica en la UTP Sede Piura se desarrolla en cuatro fases secuenciales rigurosamente auditadas. En la primera fase de diagnóstico y línea base, se evalúa el estado inicial de los proyectos de investigación mediante la lista de cotejo estructural y se registra el consentimiento informado de los estudiantes participantes. En la segunda fase de intervención tecnológica, los tesistas interactúan con el servidor MCP y el backend Django Ninja para estructurar progresivamente los treinta y dos pasos metodológicos distribuidos en siete capítulos, garantizando que cada entrega supere los validadores deterministas Pydantic y las reglas de consistencia cruzada en PostgreSQL. En la tercera fase de supervisión docente, los asesores revisan los capítulos enviados mediante el panel administrativo con anclajes de posición exactos e historial inmutable de estados hasta emitir su aprobación formal. Finalmente, en la cuarta fase de evaluación empírica y cierre estadístico, se aplica el cuestionario calibrado de usabilidad y trazabilidad metodológica junto con las pruebas inferenciales para contrastar las hipótesis formuladas.",
            "palabras_totales": 165
        }
    }
}
