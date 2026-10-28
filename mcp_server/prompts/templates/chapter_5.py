"""Plantillas de prompts para el Capítulo 5: Marco Teórico y Conceptual (P21 a P24)."""

CHAPTER_5_TEMPLATES = {
    "P21": {
        "step_code": "P21",
        "prompt_name": "paso_p21_seleccion_teorias",
        "titulo": "P21: Selección de Teorías Base",
        "descripcion": "Fundamenta el estudio en marcos teóricos consolidados, autores seminales y postulados centrales.",
        "guia_metodologica": """
Fundamentación teórica:
1. Identifica entre 1 y 4 teorías base directamente relacionadas con las variables del estudio.
2. Cada teoría requiere: nombre_teoria, autores_principales, anio_origen (1800-2026), postulado_central (mínimo 20 caracteres) y aplicabilidad_al_proyecto (mínimo 20 caracteres).
""",
        "esquema_json_ejemplo": {
            "teorias": [
                {
                    "nombre_teoria": "Teoría de la Aceptación de la Tecnología (TAM)",
                    "autores_principales": "Davis, F. D.",
                    "anio_origen": 1989,
                    "postulado_central": "La utilidad percibida y la facilidad de uso percibida determinan la intención conductual de utilizar un sistema tecnológico.",
                    "aplicabilidad_al_proyecto": "Permite modelar la adopción del protocolo MCP y la interfaz asistida por parte de tesistas y docentes universitarios."
                },
                {
                    "nombre_teoria": "Teoría de la Carga Cognitiva",
                    "autores_principales": "Sweller, J.",
                    "anio_origen": 1988,
                    "postulado_central": "La estructura de la memoria de trabajo limita la cantidad de información nueva que puede procesarse simultáneamente.",
                    "aplicabilidad_al_proyecto": "Sustenta la división de la tesis en 32 pasos desacoplados para evitar la sobrecarga cognitiva del estudiante."
                }
            ]
        }
    },
    "P22": {
        "step_code": "P22",
        "prompt_name": "paso_p22_definiciones_constructos",
        "titulo": "P22: Definición de Constructos y Conceptos Clave",
        "descripcion": "Define formalmente entre 3 y 15 constructos con autor y año de respaldo.",
        "guia_metodologica": """
Marco conceptual de constructos:
1. Define entre 3 y 15 términos clave esenciales de la investigación.
2. Cada término debe incluir:
   - termino (nombre del concepto).
   - definicion (redacción precisa de 20 a 350 caracteres).
   - cita_fuente (autor y año de referencia, ej. 'Anthropic (2024)', 'Hernández-Sampieri (2018)').
""",
        "esquema_json_ejemplo": {
            "constructos": [
                {
                    "termino": "Model Context Protocol (MCP)",
                    "definicion": "Protocolo estándar abierto que permite la comunicación segura y estructurada entre aplicaciones cliente de IA y servidores de datos deterministas.",
                    "cita_fuente": "Anthropic (2024)"
                },
                {
                    "termino": "Alucinación en Modelos de Lenguaje",
                    "definicion": "Generación de información fáctica o referencias bibliográficas sintéticas plausibles pero inexistentes o no verificadas en la realidad.",
                    "cita_fuente": "Ji et al. (2023)"
                },
                {
                    "termino": "Matriz de Consistencia Metodológica",
                    "definicion": "Herramienta que articula con correspondencia biunívoca el problema, objetivos, hipótesis, variables e indicadores de una tesis.",
                    "cita_fuente": "Carrasco (2019)"
                }
            ]
        }
    },
    "P23": {
        "step_code": "P23",
        "prompt_name": "paso_p23_modelo_conceptual",
        "titulo": "P23: Modelo Conceptual y Relacional (Diagrama Mermaid)",
        "descripcion": "Representa la interacción causal y operativa entre variables con descripción y diagrama Mermaid.",
        "guia_metodologica": """
Modelado conceptual de la investigación:
1. descripcion_relaciones: explicación de 40 a 800 caracteres sobre cómo interactúan las variables independientes, dependientes y moderadoras.
2. diagrama_mermaid: código Mermaid válido (`flowchart LR` o `graph TD`) que ilustre visualmente la relación de entrada, proceso, protocolo y salidas académicas.
""",
        "esquema_json_ejemplo": {
            "descripcion_relaciones": "El Sistema Web con Protocolo MCP actúa como variable independiente tecnológica que interviene directamente sobre la formulación metodológica de tesis (variable dependiente), estructurando la consistencia interna y garantizando la fidelidad documental.",
            "diagrama_mermaid": "graph LR\n    VI[Sistema Web con Protocolo MCP] -->|Estandariza| P[Validación Determinista Zero-LLM]\n    P -->|Garantiza| VD[Formulación Metodológica de Tesis]\n    VD --> R1[Consistencia Biunívoca]\n    VD --> R2[Citas Grounded sin Alucinaciones]"
        }
    },
    "P24": {
        "step_code": "P24",
        "prompt_name": "paso_p24_proposiciones_derivadas",
        "titulo": "P24: Proposiciones Teóricas Derivadas",
        "descripcion": "Deduce argumentos teóricos que conectan las teorías base con las hipótesis de investigación.",
        "guia_metodologica": """
Deducción de proposiciones teóricas:
1. Formula entre 2 y 8 proposiciones lógicas derivadas que enlacen los marcos teóricos (TAM, Carga Cognitiva) con las hipótesis de la tesis.
2. Cada proposición debe sustentar por qué la intervención tecnológica generará los efectos previstos.
""",
        "esquema_json_ejemplo": {
            "proposiciones_teoricas": [
                "A mayor estructuración determinista en la interfaz del estudiante, menor sobrecarga cognitiva y menor dispersión en el planteamiento del problema.",
                "La verificación de citas mediante contratos Pydantic inflexibles inhibe la persistencia de referencias sintéticas en el repositorio académico.",
                "La retroalimentación docente con comentarios anclados en coordenadas de texto reduce la ambigüedad y acelera la aprobación de capítulos."
            ]
        }
    }
}
