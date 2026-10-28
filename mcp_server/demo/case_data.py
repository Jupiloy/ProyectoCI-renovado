"""Caso de ejemplo para ejecutar los pasos metodológicos por MCP."""


def _construir_payloads_32_pasos(source_info: dict | None = None) -> dict[str, tuple[str, dict]]:
    """Retorna (content_md, output_data) de P01 a P32 basados en la problemática real de TesisMCP."""
    excerpt_id = (source_info or {}).get("first_excerpt_id") or 1
    source_title = (source_info or {}).get("title") or "Accelerating Scientific Research Through a Multi-LLM Framework"
    source_doi = (source_info or {}).get("doi") or "10.48550/arXiv.2502.07960"
    page_count = (source_info or {}).get("page_count") or 34
    titulo_oficial = (
        "Sistema Web con Protocolo MCP para la Formulación Metodológica de Tesis "
        "en Estudiantes de la UTP Piura, 2026"
    )
    # 18 palabras exactas; contiene:
    # - variables_confirmadas: ["Protocolo MCP", "Formulación Metodológica de Tesis"]
    # - unidad_analisis_confirmada: "Estudiantes"
    # - lugar_confirmado: "UTP Piura"
    # - periodo_confirmado: 2026

    p05_parrafos = [
        (
            "En el contexto global de la educación superior, la elaboración de trabajos de investigación "
            "para la obtención del grado académico enfrenta cuellos de botella estructurales derivados de "
            "la desconexión entre la escritura académica y las reglas metodológicas institucionales. Aunque "
            "los modelos de lenguaje de gran escala han agilizado la redacción preliminar, los estudios "
            "recientes demuestran que la generación libre de texto largo introduce alucinaciones bibliográficas "
            "severas y pérdida de coherencia entre objetivos, variables e instrumentos de medición."
        ),
        (
            "A nivel nacional en el Perú, diversas universidades han implementado repositorios digitales y "
            "plataformas web administrativas para el control de trámites de titulación, logrando reducir los "
            "tiempos de registro documental y seguimiento de expedientes. Sin embargo, dichas soluciones se "
            "limitan a la gestión de archivos estáticos en formato PDF o Word sin inspeccionar ni validar "
            "la consistencia interna de la matriz metodológica, dejando toda la carga de verificación "
            "estructural en revisiones manuales asíncronas."
        ),
        (
            "En el ámbito local de la Universidad Tecnológica del Perú (UTP) Sede Piura durante el ciclo 2026, "
            "los estudiantes de Ingeniería de Sistemas e Informática elaboran sus proyectos del Curso Integrador "
            "utilizando procesadores de texto aislados y chats conversacionales sin memoria canónica. Esta "
            "fragmentación provoca que los asesores inviertan gran parte de las sesiones corrigiendo errores "
            "de forma, verbos mal formulados, variables huérfanas y citas no verificadas en lugar de profundizar "
            "en el rigor técnico y científico de la solución propuesta."
        ),
        (
            "Frente a esta problemática, resulta imperativo diseñar e implementar una arquitectura híbrida "
            "desacoplada basada en el Model Context Protocol (MCP) que separe la generación asistida por IA "
            "de la validación determinista en servidor (Zero-LLM). De este modo, cada paso metodológico desde "
            "el Capítulo 1 hasta el Capítulo 7 queda resguardado por contratos estrictos, bloqueo optimista y "
            "trazabilidad directa hacia fuentes primarias verificadas en texto completo."
        ),
    ]
    p05_md = "\n\n".join(p05_parrafos)
    p05_words = len(p05_md.split())

    p29_md = (
        "El procedimiento de ejecución metodológica en la UTP Sede Piura se desarrolla en cuatro fases "
        "secuenciales rigurosamente auditadas. En la primera fase de diagnóstico y línea base, se evalúa el "
        "estado inicial de los proyectos de investigación mediante la lista de cotejo estructural y se "
        "registra el consentimiento informado de los estudiantes participantes. En la segunda fase de "
        "intervención tecnológica, los tesistas interactúan con el servidor MCP y el backend Django Ninja "
        "para estructurar progresivamente los treinta y dos pasos metodológicos distribuidos en siete "
        "capítulos, garantizando que cada entrega supere los validadores deterministas Pydantic y las "
        "reglas de consistencia cruzada en PostgreSQL. En la tercera fase de supervisión docente, los "
        "asesores revisan los capítulos enviados mediante el panel administrativo con anclajes de posición "
        "exactos e historial inmutable de estados hasta emitir su aprobación formal. Finalmente, en la "
        "cuarta fase de evaluación empírica y cierre estadístico, se aplica el cuestionario calibrado de "
        "usabilidad y trazabilidad metodológica junto con las pruebas inferenciales para contrastar las "
        "hipótesis formuladas."
    )
    p29_words = len(p29_md.split())

    return {
        "P01": (
            "# P01: Sondeo y Preselección de Temas\nExploración de 5 candidatos tecnológicos en UTP Sede Piura.",
            {
                "temas_propuestos": [
                    {
                        "id": 1,
                        "titulo_tentativo": "Sistema Web con Protocolo MCP para la Formulación Metodológica de Tesis",
                        "pros": ["Acceso directo a cohorte UTP Piura", "Alto impacto en reducción de alucinaciones"],
                        "contras": ["Requiere orquestación estricta entre stdio y PostgreSQL"],
                        "viabilidad_preliminar": "ALTA",
                    },
                    {
                        "id": 2,
                        "titulo_tentativo": "Aplicativo móvil con reconocimiento facial para control de asistencia estudiantil",
                        "pros": ["Hardware disponible en smartphones"],
                        "contras": ["Tema saturado en repositorios locales y restricciones de privacidad biométrica"],
                        "viabilidad_preliminar": "MEDIA",
                    },
                    {
                        "id": 3,
                        "titulo_tentativo": "Sistema predictivo de deserción universitaria mediante redes neuronales profundas",
                        "pros": ["Relevancia institucional"],
                        "contras": ["Datos históricos socioeconómicos restringidos por protección de datos personales"],
                        "viabilidad_preliminar": "BAJA",
                    },
                    {
                        "id": 4,
                        "titulo_tentativo": "Plataforma IoT para monitoreo energético en laboratorios de cómputo",
                        "pros": ["Medición en tiempo real"],
                        "contras": ["Dependencia de adquisición de sensores industriales e instalación eléctrica"],
                        "viabilidad_preliminar": "MEDIA",
                    },
                    {
                        "id": 5,
                        "titulo_tentativo": "Chatbot de consultas administrativas para trámites de matrícula universitaria",
                        "pros": ["Implementación rápida"],
                        "contras": ["Bajo aporte metodológico y alcance meramente informativo"],
                        "viabilidad_preliminar": "MEDIA",
                    },
                ],
                "tema_preseleccionado_id": 1,
            },
        ),
        "P02": (
            "# P02: Matriz de Evaluación Comparativa de Temas\nSelección objetiva del tema ganador (ID 1).",
            {
                "matriz_comparativa": [
                    {
                        "tema_id": 1,
                        "titulo": "Sistema Web con Protocolo MCP para la Formulación Metodológica de Tesis",
                        "puntajes": {
                            "acceso_a_datos": 5,
                            "relevancia_profesional": 5,
                            "brecha_conocimiento": 5,
                            "recursos_disponibles": 4,
                        },
                        "puntaje_total": 19,
                        "justificacion_eleccion": "Acceso total a casos de prueba en UTP Sede Piura y brecha clara en arquitecturas MCP con validación Zero-LLM.",
                    },
                    {
                        "tema_id": 2,
                        "titulo": "Aplicativo móvil con reconocimiento facial para control de asistencia estudiantil",
                        "puntajes": {
                            "acceso_a_datos": 3,
                            "relevancia_profesional": 3,
                            "brecha_conocimiento": 2,
                            "recursos_disponibles": 4,
                        },
                        "puntaje_total": 12,
                        "justificacion_eleccion": "Existen múltiples implementaciones previas en la región Piura con baja novedad científica.",
                    },
                    {
                        "tema_id": 4,
                        "titulo": "Plataforma IoT para monitoreo energético en laboratorios de cómputo",
                        "puntajes": {
                            "acceso_a_datos": 3,
                            "relevancia_profesional": 4,
                            "brecha_conocimiento": 3,
                            "recursos_disponibles": 2,
                        },
                        "puntaje_total": 12,
                        "justificacion_eleccion": "Limitaciones presupuestarias y de permisos físicos para intervenir tableros eléctricos.",
                    },
                ],
                "tema_ganador_id": 1,
                "tema_ganador_titulo": "Sistema Web con Protocolo MCP para la Formulación Metodológica de Tesis",
            },
        ),
        "P03": (
            "# P03: Alineación con ODS y Líneas de Investigación UTP\nVinculado con el ODS 4 (Educación de Calidad).",
            {
                "ods_principal_numero": 4,
                "ods_principal_nombre": "Educación de Calidad",
                "meta_ods_especifica": "4.4",
                "argumento_alineacion": "Fortalece las competencias investigativas y tecnológicas de los estudiantes universitarios mediante una arquitectura verificable que previene alucinaciones en trabajos de grado.",
                "linea_utp_vinculada": "Tecnologías Emergentes aplicadas a la Educación Superior y Gestión del Conocimiento",
            },
        ),
        "P04": (
            f"# P04: Delimitación Formal del Título\nTítulo oficial confirmado: **{titulo_oficial}** (18 palabras).",
            {
                "titulo_oficial": titulo_oficial,
                "conteo_palabras": 18,
                "variables_confirmadas": ["Protocolo MCP", "Formulación Metodológica de Tesis"],
                "unidad_analisis_confirmada": "Estudiantes",
                "lugar_confirmado": "UTP Piura",
                "periodo_confirmado": 2026,
            },
        ),
        "P05": (
            p05_md,
            {
                "contenido_markdown": p05_md,
                "num_parrafos": 4,
                "palabras_totales": p05_words,
            },
        ),
        "P06": (
            "# P06: Árbol de Problemas y Formulación de Preguntas\nSincronización inicial de la Matriz de Consistencia.",
            {
                "problema_central": "Alta incidencia de inconsistencias estructurales y alucinaciones bibliográficas en la formulación metodológica de tesis en estudiantes universitarios.",
                "causas_directas": [
                    "Uso de asistentes conversacionales sin validación determinista de esquemas ni estado canónico",
                    "Desconexión entre las matrices de consistencia, operacionalización y los instrumentos de medición",
                    "Revisiones docentes manuales sobre documentos estáticos sin trazabilidad de cambios ni fuentes",
                ],
                "efectos_directos": [
                    "Retrasos recurrentes en la aprobación de capítulos y sobrecarga de correcciones repetitivas",
                    "Riesgo de incorporar citas o métricas inexistentes en los borradores académicos",
                    "Frustración estudiantil y dilatación en el proceso de titulación profesional",
                ],
                "pregunta_general": "¿De qué manera el Protocolo MCP optimiza la Formulación Metodológica de Tesis en estudiantes de la UTP Piura, 2026?",
                "preguntas_especificas": [
                    "¿Cómo influye la validación determinista de contratos en la coherencia estructural de la matriz de consistencia?",
                    "¿En qué medida la verificación documental en texto completo reduce la inclusión de fuentes no comprobadas?",
                    "¿Cómo impacta el flujo de revisión con anclajes inmutables en la resolución de observaciones del asesor?",
                ],
            },
        ),
        "P07": (
            "# P07: Justificación en Cuatro Dimensiones\nSustento teórico, práctico, metodológico y social.",
            {
                "justificaciones": [
                    {
                        "dimension": "TEORICA",
                        "argumento": "Aporta un modelo arquitectónico que integra el protocolo abierto MCP con invariantes de dominio relacionales para acotar sistemas multi-agente en tareas de escritura científica compleja.",
                    },
                    {
                        "dimension": "PRACTICA",
                        "argumento": "Proporciona a los tesistas y asesores de la UTP Sede Piura una plataforma centralizada que automatiza la verificación estructural de los 32 pasos metodológicos y agiliza la retroalimentación docente.",
                    },
                    {
                        "dimension": "METODOLOGICA",
                        "argumento": "Demuestra que la separación estricta entre la generación asistida por lenguaje natural y los validadores deterministas Zero-LLM garantiza la trazabilidad entre variables, dimensiones, indicadores e ítems.",
                    },
                    {
                        "dimension": "SOCIAL",
                        "argumento": "Democratiza el acompañamiento metodológico riguroso en estudiantes de ingeniería de la región Piura, reduciendo las brechas formativas y elevando la calidad de la producción académica local.",
                    },
                ],
                "resumen_ejecutivo": "El proyecto TesisMCP se justifica integralmente al resolver la tensión entre la asistencia generativa de IA y el rigor científico universitario mediante contratos verificables, auditoría física de fuentes y supervisión docente auditable.",
            },
        ),
        "P08": (
            "# P08: Brecha de Investigación y Aporte Propuesto\nDefinición del vacío tecnológico y estado de evidencia.",
            {
                "brecha_detectada": "Los sistemas web universitarios locales solo gestionan trámites administrativos, mientras que los frameworks multi-LLM carecen de persistencia relacional canónica y reportan altas tasas de alucinación bibliográfica.",
                "aporte_propuesto": "Una plataforma web con arquitectura desacoplada y servidor MCP que valida determinísticamente 32 pasos metodológicos en 27 tablas PostgreSQL con trazabilidad de fuentes a página física.",
                "estado_evidencia": "PENDING_EVIDENCE",
            },
        ),
        "P09": (
            "# P09: Formulación de Objetivos (Taxonomía de Bloom)\nAlineación 1 a 1 con las preguntas de investigación.",
            {
                "objetivo_general": "Determinar de qué manera el Protocolo MCP optimiza la Formulación Metodológica de Tesis en estudiantes de la UTP Piura, 2026",
                "objetivos_especificos": [
                    "Analizar la influencia de la validación determinista de contratos en la coherencia estructural de la matriz de consistencia",
                    "Evaluar el efecto de la verificación documental en texto completo sobre la reducción de fuentes no comprobadas",
                    "Demostrar el impacto del flujo de revisión con anclajes inmutables en la resolución de observaciones del asesor",
                ],
            },
        ),
        "P10": (
            "# P10: Consolidación de Preguntas de Investigación\nSincronización canónica en ConsistencyRow.",
            {
                "pregunta_general": "¿De qué manera el Protocolo MCP optimiza la Formulación Metodológica de Tesis en estudiantes de la UTP Piura, 2026?",
                "preguntas_especificas": [
                    "¿Cómo influye la validación determinista de contratos en la coherencia estructural de la matriz de consistencia?",
                    "¿En qué medida la verificación documental en texto completo reduce la inclusión de fuentes no comprobadas?",
                    "¿Cómo impacta el flujo de revisión con anclajes inmutables en la resolución de observaciones del asesor?",
                ],
            },
        ),
        "P11": (
            "# P11: Formulación de Hipótesis y Variables Relacionales\nMaterialización en ResearchVariable y ConsistencyRowVariable.",
            {
                "tipo_investigacion": "EXPLICATIVA",
                "hipotesis_general": "La arquitectura basada en el Protocolo MCP optimiza significativamente la Formulación Metodológica de Tesis en estudiantes de la UTP Piura, 2026.",
                "hipotesis_especificas": [
                    "La validación determinista de contratos incrementa significativamente la coherencia estructural de la matriz de consistencia.",
                    "La verificación documental en texto completo disminuye significativamente la inclusión de fuentes no comprobadas.",
                    "El flujo de revisión con anclajes inmutables mejora significativamente la tasa de resolución de observaciones del asesor.",
                ],
                "variable_independiente": "Protocolo MCP",
                "variable_dependiente": "Formulación Metodológica de Tesis",
            },
        ),
        "P12": (
            "# P12: Matriz de Operacionalización de Variables\nMaterialización de Dimensiones (VariableDimension) e Indicadores (Indicator).",
            {
                "matriz_operacionalizacion": [
                    {
                        "variable": "Protocolo MCP",
                        "definicion_conceptual": "Estándar de comunicación desacoplada que conecta agentes de lenguaje con herramientas y validadores deterministas del dominio académico.",
                        "definicion_operacional": "Evaluación técnica y perceptual de la validación de contratos Pydantic, verificación de fuentes y control de concurrencia optimista.",
                        "dimensiones": ["Validación Determinista", "Grounding Documental"],
                        "indicadores": ["Cumplimiento de contratos por paso", "Tasa de verificación de fuentes PDF"],
                        "escala_medicion": "ORDINAL",
                    },
                    {
                        "variable": "Formulación Metodológica de Tesis",
                        "definicion_conceptual": "Proceso sistemático de estructuración coherente de problemas, objetivos, hipótesis, variables e instrumentos de investigación universitaria.",
                        "definicion_operacional": "Medición de la consistencia cruzada entre capítulos y la eficiencia en el levantamiento de observaciones del asesor docente.",
                        "dimensiones": ["Coherencia Estructural", "Eficiencia de Revisión Docente"],
                        "indicadores": ["Índice de trazabilidad de la matriz", "Resolución efectiva de observaciones"],
                        "escala_medicion": "ORDINAL",
                    },
                ]
            },
        ),
        "P13": (
            "# P13: Estrategia y Ecuaciones de Búsqueda Bibliográfica\nEcuaciones booleanas para Scopus e IEEE Xplore.",
            {
                "ecuacion_scopus": 'TITLE-ABS-KEY(("Model Context Protocol" OR "Multi-LLM" OR "AI Agent") AND ("academic writing" OR "thesis management" OR "scientific research"))',
                "ecuacion_ieee": '("Large Language Models" OR "Multi-Agent Systems") AND ("Thesis Supervision" OR "Deterministic Validation" OR "Grounded Generation")',
                "palabras_clave_es": ["Protocolo MCP", "Gestión de Tesis", "Validación Determinista", "Trazabilidad Académica"],
                "palabras_clave_en": ["Model Context Protocol", "Thesis Management", "Multi-Agent Systems", "Grounded Truth"],
            },
        ),
        "P14": (
            "# P14: Criterios de Inclusión y Exclusión (Ventana Temporal 2021–2026)",
            {
                "criterios_inclusion": [
                    "Estudios empíricos o arquitecturas de software publicados entre 2021 y 2026",
                    "Artículos y tesis con acceso a PDF a texto completo verificable",
                    "Investigaciones enfocadas en sistemas de gestión de tesis o escritura científica asistida por IA",
                ],
                "criterios_exclusion": [
                    "Artículos de opinión, resúmenes sin texto completo o blogs no arbitrados",
                    "Trabajos fuera del rango temporal 2021-2026",
                    "Fuentes cuyos metadatos o conteo físico de páginas no puedan ser auditados",
                ],
                "anio_inicio": 2021,
                "anio_fin": 2026,
                "idiomas_admitidos": ["Español", "Inglés"],
            },
        ),
        "P15": (
            "# P15: Embudo de Selección PRISMA\nCribado riguroso hasta el estudio núcleo del estado del arte verificado en este lote.",
            {
                "registros_identificados": 48,
                "registros_duplicados_removidos": 8,
                "registros_cribados": 40,
                "articulos_evaluados_texto_completo": 14,
                "estudios_incluidos": 1,
            },
        ),
        "P16": (
            "# P16: Matriz de Antecedentes Verificados en Texto Completo\nCotejo obligatorio contra SourceDocument (Status=TEXT_CHECKED).",
            {
                "estudios": [
                    {
                        "autores": "Joaquin Ramirez-Medina, Mohammadmehdi Ataei, Alidad Amirfazli",
                        "anio": 2025,
                        "titulo": source_title,
                        "metodologia": "Experimental computacional con orquestación Multi-LLM (ARIA)",
                        "muestra": "Flujos de investigación científica automatizada y caso de estudio",
                        "hallazgo_principal": "Demuestra aceleración en tareas de revisión científica en menos de una hora con supervisión del usuario.",
                        "doi": source_doi,
                        "verification_level": "TEXT_EXTRACTED_WITH_QUOTES",
                        "paginas_reales": page_count,
                        "metodologia_evidencia": {
                            "excerpt_id": excerpt_id,
                            "cita_textual": "Artificial Research Innovator Assistant\n(ARIA), a four-agent, multi-LLM framework.",
                        },
                        "muestra_evidencia": {
                            "excerpt_id": excerpt_id,
                            "cita_textual": "In a case study on dropwise condensation enhancement,\nARIA demonstrates its capability to streamline research tasks within an hour",
                        },
                        "hallazgo_evidencia": {
                            "excerpt_id": excerpt_id,
                            "cita_textual": "streamline research tasks within an hour, maintaining\nuser oversight during execution and ultimately liberating researchers from time-intensive\ntasks.",
                        },
                    }
                ]
            },
        ),
        "P17": (
            "# P17: Síntesis Temática de la Literatura\nEjes, consensos y debates identificados.",
            {
                "ejes_tematicos": [
                    "Orquestación multi-agente y planificación cognitiva en escritura científica",
                    "Sistemas web universitarios para el control y seguimiento de tesis en el Perú",
                    "Verificación empírica de fuentes y mitigación de alucinaciones bibliográficas",
                ],
                "consensos_literatura": [
                    "Los sistemas web institucionales reducen la fricción administrativa en el seguimiento de tesis",
                    "La descomposición en sub-etapas supera a la generación monolítica en textos académicos largos",
                ],
                "discrepancias_o_debates": [
                    "Los sistemas multi-LLM puros generan alta fluidez textual pero sufren tasas críticas de alucinación en citas si no cuentan con validadores deterministas externos",
                ],
            },
        ),
        "P18": (
            "# P18: Identificación del Vacío de Conocimiento",
            {
                "vacio_conocimiento_identificado": "Inexistencia de una plataforma universitaria que fusione el protocolo abierto MCP con validación determinista Zero-LLM de los 32 pasos metodológicos y auditoría física de PDFs en PostgreSQL.",
                "justificacion_necesidad_estudio": "Se requiere demostrar empíricamente en la UTP Sede Piura que el desacoplamiento entre asistente IA y reglas de dominio elimina las inconsistencias de matriz y las citas inventadas.",
            },
        ),
        "P19": (
            "# P19: Redacción Articulada de Antecedentes Internacionales y Nacionales",
            {
                "antecedentes_internacionales": (
                    "En el plano internacional, el marco multi-agente ARIA (2025) "
                    "evidencia que estructurar el proceso investigativo en fases cognitivas "
                    "especializadas permite automatizar la búsqueda, filtrado y síntesis científica, "
                    "acelerando la revisión de literatura en menos de una hora frente a flujos manuales."
                ),
                "antecedentes_nacionales": (
                    "En el contexto peruano y regional de Piura, las investigaciones institucionales "
                    "confirman el valor de centralizar el seguimiento de tesis y el control metodológico "
                    "en plataformas estructuradas, integrando el protocolo abierto MCP con validación determinista."
                ),
                "sintesis_comparativa": (
                    "Mientras los estudios internacionales como ARIA aportan el paradigma multi-agente "
                    "para acelerar la síntesis documental, TesisMCP traslada esa capacidad al ámbito "
                    "universitario con estricto control determinista de citas y páginas comprobadas."
                ),
            },
        ),
        "P20": (
            "# P20: Consolidación de Referencias Bibliográficas Verificadas",
            {
                "estilo_citacion": "APA_7",
                "referencias_formateadas": [
                    "Ramirez-Medina, J., Ataei, M., & Amirfazli, A. (2025). Accelerating scientific research through a multi-LLM framework. arXiv. https://doi.org/10.48550/arXiv.2502.07960",
                ],
            },
        ),
        "P21": (
            "# P21: Teorías Base del Marco Teórico",
            {
                "teorias": [
                    {
                        "nombre_teoria": "Modelo Cognitivo de Procesos de Escritura (Flower y Hayes)",
                        "autores_principales": "Linda Flower y John R. Hayes",
                        "anio_origen": 1981,
                        "postulado_central": "La escritura experta no es lineal, sino un proceso jerárquico regulado por metas que alterna planificación, traducción y revisión continua.",
                        "aplicabilidad_al_proyecto": "Sustenta la descomposición del proyecto de tesis en 32 pasos iterativos con compuertas de validación y revisión del asesor.",
                    },
                    {
                        "nombre_teoria": "Arquitectura Limpia y Diseño Guiado por el Dominio (DDD)",
                        "autores_principales": "Robert C. Martin y Eric Evans",
                        "anio_origen": 2003,
                        "postulado_central": "Las reglas de negocio e invariantes del dominio deben residir en un núcleo puro e independiente de las interfaces de usuario, agentes externos o bases de datos.",
                        "aplicabilidad_al_proyecto": "Fundamenta que tanto la interfaz web como el servidor MCP deleguen toda operación en la capa transaccional thesis.services.",
                    },
                ]
            },
        ),
        "P22": (
            "# P22: Marco Conceptual (Definición de Constructos y Variables)",
            {
                "constructos": [
                    {
                        "termino": "Protocolo MCP",
                        "definicion": "Protocolo estándar abierto que permite exponer herramientas tipadas y recursos de contexto a modelos de lenguaje bajo control estricto del servidor.",
                        "cita_fuente": "Anthropic (2024)",
                    },
                    {
                        "termino": "Formulación Metodológica de Tesis",
                        "definicion": "Estructuración rigurosa y coherente de los componentes del método científico aplicados a un proyecto de investigación universitaria.",
                        "cita_fuente": "Hernández-Sampieri y Mendoza (2018)",
                    },
                    {
                        "termino": "Validación Determinista Zero-LLM",
                        "definicion": "Verificación algorítmica reproducible mediante esquemas tipados y consultas relacionales que no depende de juicios probabilísticos de un modelo de lenguaje.",
                        "cita_fuente": "Elaboración propia (2026)",
                    },
                ]
            },
        ),
        "P23": (
            "# P23: Modelo Teórico-Relacional y Diagrama Estructural",
            {
                "descripcion_relaciones": "El Protocolo MCP actúa como variable independiente que regula la interacción entre el estudiante y el núcleo de dominio, impactando directamente en la calidad y consistencia de la Formulación Metodológica de Tesis.",
                "diagrama_mermaid": "flowchart LR\n  MCP[\"Protocolo MCP (VI)\"] --> VAL[\"Validadores Zero-LLM\"]\n  VAL --> FMT[\"Formulación Metodológica de Tesis (VD)\"]",
            },
        ),
        "P24": (
            "# P24: Proposiciones Teóricas Derivadas del Marco",
            {
                "proposiciones_teoricas": [
                    "Todo paso metodológico validado mediante contratos estrictos preserva la cardinalidad de la matriz de consistencia.",
                    "El bloqueo de citas carentes de registro verificable en SourceDocument impide la propagación de referencias alucinadas al informe final.",
                    "El anclaje de observaciones docentes por código de punto y hash SHA-256 garantiza la auditabilidad de las correcciones.",
                ]
            },
        ),
        "P25": (
            "# P25: Diseño Metodológico de la Investigación",
            {
                "enfoque": "CUANTITATIVO",
                "diseno": "CUASIEXPERIMENTAL",
                "nivel_alcance": "EXPLICATIVO",
                "corte_temporal": "TRANSVERSAL",
                "justificacion_diseno": "Se emplea un enfoque cuantitativo de alcance explicativo y diseño cuasiexperimental para medir y demostrar el efecto del sistema TesisMCP sobre la calidad estructural y consistencia de los proyectos formulados.",
            },
        ),
        "P26": (
            "# P26: Técnicas e Instrumentos de Recolección de Datos",
            {
                "tecnicas_seleccionadas": [
                    "Encuesta estructurada a tesistas y asesores",
                    "Análisis documental automatizado de matrices y borradores en base de datos",
                ],
                "instrumentos_previstos": [
                    "Cuestionario de Rigor Metodológico y Usabilidad con escala Likert de 5 puntos",
                    "Guía de entrevista semiestructurada para docentes asesores",
                ],
                "procedimiento_recoleccion": "Los datos se recolectan al finalizar la formulación de los siete capítulos en el entorno controlado de la UTP Sede Piura, registrando tanto las métricas transaccionales del sistema como la evaluación de los usuarios.",
            },
        ),
        "P27": (
            "# P27: Validez y Confiabilidad de los Instrumentos",
            {
                "validez_instrumento": "JUICIO_EXPERTOS_AIKEN",
                "confiabilidad_metodo": "ALFA_CRONBACH",
                "criterio_aceptabilidad": "Coeficiente V de Aiken >= 0.80 para validez de contenido por jueces expertos y Alfa de Cronbach >= 0.70 en prueba piloto.",
            },
        ),
        "P28": (
            "# P28: Aspectos Éticos y Protección de Datos",
            {
                "consentimiento_informado_requerido": True,
                "principios_eticos_aplicados": [
                    "Consentimiento informado previo y voluntario de los participantes",
                    "Anonimización de identidades en los reportes estadísticos agregados",
                    "Transparencia e integridad científica (Grounded Truth sin fabricación de datos)",
                ],
                "politica_confidencialidad_datos": "Los proyectos, borradores y tokens criptográficos se resguardan con control de acceso por membresía y hash SHA-256 en PostgreSQL, cumpliendo la Ley N.° 29733 de Protección de Datos Personales del Perú.",
            },
        ),
        "P29": (
            p29_md,
            {
                "contenido_markdown": p29_md,
                "palabras_totales": p29_words,
            },
        ),
        "P30": (
            "# P30: Construcción del Cuestionario y Trazabilidad a Indicadores de P12",
            {
                "nombre_instrumento": "Cuestionario de Evaluación de Protocolo MCP y Formulación Metodológica",
                "poblacion_objetivo": "Estudiantes de Ingeniería de Sistemas e Informática de la UTP Sede Piura",
                "banco_items": [
                    {
                        "numero": 1,
                        "dimension_asociada": "Validación Determinista",
                        "indicador": "Cumplimiento de contratos por paso",
                        "enunciado_reactivo": "El servidor MCP detecta oportunamente cuando falta un campo obligatorio o el conteo de palabras no coincide en un paso metodológico.",
                        "tipo_escala": "LIKERT_5",
                    },
                    {
                        "numero": 2,
                        "dimension_asociada": "Validación Determinista",
                        "indicador": "Cumplimiento de contratos por paso",
                        "enunciado_reactivo": "Las reglas automáticas impiden avanzar al siguiente capítulo si los objetivos no inician con un verbo válido de la taxonomía de Bloom.",
                        "tipo_escala": "LIKERT_5",
                    },
                    {
                        "numero": 3,
                        "dimension_asociada": "Grounding Documental",
                        "indicador": "Tasa de verificación de fuentes PDF",
                        "enunciado_reactivo": "El sistema exige que cada antecedente registrado en la matriz cuente con respaldo documental verificado antes de ser aceptado.",
                        "tipo_escala": "LIKERT_5",
                    },
                    {
                        "numero": 4,
                        "dimension_asociada": "Coherencia Estructural",
                        "indicador": "Índice de trazabilidad de la matriz",
                        "enunciado_reactivo": "La plataforma mantiene sincronizadas las preguntas, objetivos, hipótesis y variables en la matriz de consistencia sin contradicciones.",
                        "tipo_escala": "LIKERT_5",
                    },
                    {
                        "numero": 5,
                        "dimension_asociada": "Eficiencia de Revisión Docente",
                        "indicador": "Resolución efectiva de observaciones",
                        "enunciado_reactivo": "Las observaciones ancladas por el asesor permiten identificar con exactitud el fragmento que requiere corrección en cada capítulo.",
                        "tipo_escala": "LIKERT_5",
                    },
                ],
            },
        ),
        "P31": (
            "# P31: Guía de Entrevista Semiestructurada para Asesores",
            {
                "nombre_guia": "Guía de Entrevista para Docentes Asesores sobre Supervisión con TesisMCP",
                "perfil_informante_clave": "Docentes asesores del Curso Integrador y Proyecto de Tesis en Ingeniería de Sistemas (UTP Sede Piura)",
                "preguntas": [
                    {
                        "numero": 1,
                        "eje_tematico": "Validación Determinista",
                        "pregunta_principal": "¿De qué manera la validación previa de contratos Pydantic cambia la calidad inicial de los borradores que recibe para revisión?",
                        "repregunta_profundizacion": "¿Qué errores recurrentes de formato dejaron de presentarse en las entregas de los estudiantes?",
                    },
                    {
                        "numero": 2,
                        "eje_tematico": "Grounding Documental",
                        "pregunta_principal": "¿Cómo valora el bloqueo automático de antecedentes que no cuentan con PDF ni metadatos verificados en el proyecto?",
                        "repregunta_profundizacion": "¿Considera que este filtro previene eficazmente las alucinaciones bibliográficas generadas por IA?",
                    },
                    {
                        "numero": 3,
                        "eje_tematico": "Eficiencia de Revisión Docente",
                        "pregunta_principal": "¿Cómo influye el sistema de comentarios anclados e inmutables en el tiempo que dedica a aprobar cada capítulo?",
                        "repregunta_profundizacion": "¿Qué ventajas percibe frente a la revisión tradicional en archivos Word sueltos?",
                    },
                ],
            },
        ),
        "P32": (
            "# P32: Validación Piloto y Calibración Psicométrica de Instrumentos",
            {
                "tamanio_muestra_piloto": 20,
                "coeficiente_confiabilidad_obtenido": 0.89,
                "ajustes_redaccion_items": [
                    "Se precisó el término 'contratos por paso' en el ítem 1 para mayor claridad de los estudiantes de séptimo ciclo",
                    "Se añadió un ejemplo visual de observación anclada en las instrucciones del ítem 5",
                ],
                "estado_instrumento": "CALIBRADO",
            },
        ),
    }
