"""Plantillas de prompts para el Capítulo 7: Instrumentos de Recolección de Datos (P30 a P32)."""

CHAPTER_7_TEMPLATES = {
    "P30": {
        "step_code": "P30",
        "prompt_name": "paso_p30_cuestionario_likert",
        "titulo": "P30: Cuestionario Cuantitativo en Escala Likert",
        "descripcion": "Diseña un banco de ítems (mínimo 5) trazables directamente a las dimensiones e indicadores de P12.",
        "guia_metodologica": """
Diseño de reactivos cuantitativos:
1. nombre_instrumento: denominación formal del instrumento (5 a 150 caracteres).
2. poblacion_objetivo: descripción de los sujetos que responderán (5 a 150 caracteres, ej. 'Estudiantes de ingeniería de la UTP Piura').
3. banco_items: entre 5 y 60 reactivos numerados correlativamente.
4. Cada ítem debe indicar:
   - numero: entero del 1 al 60.
   - dimension_asociada: nombre de la dimensión (debe coincidir con la matriz de operacionalización P12).
   - indicador: nombre del indicador evaluado.
   - enunciado_reactivo: redacción del ítem en afirmación (10 a 300 caracteres).
   - tipo_escala: 'LIKERT_5', 'LIKERT_7' o 'DICOTOMICA'.
""",
        "esquema_json_ejemplo": {
            "nombre_instrumento": "Cuestionario de Usabilidad y Consistencia de Formulación de Tesis",
            "poblacion_objetivo": "Estudiantes de ingeniería de sistemas participantes del Curso Integrador en UTP Piura",
            "banco_items": [
                {
                    "numero": 1,
                    "dimension_asociada": "Consistencia Metodológica",
                    "indicador": "Índice de coherencia biunívoca en matriz",
                    "enunciado_reactivo": "El asistente me ayuda a formular objetivos que corresponden directamente con las preguntas planteadas.",
                    "tipo_escala": "LIKERT_5"
                },
                {
                    "numero": 2,
                    "dimension_asociada": "Consistencia Metodológica",
                    "indicador": "Índice de coherencia biunívoca en matriz",
                    "enunciado_reactivo": "La plataforma valida que cada variable cuente con dimensiones e indicadores medibles.",
                    "tipo_escala": "LIKERT_5"
                },
                {
                    "numero": 3,
                    "dimension_asociada": "Fidelidad Documental Grounded",
                    "indicador": "Porcentaje de citas respaldadas en texto completo de PDFs",
                    "enunciado_reactivo": "Las referencias de antecedentes sugeridas por el sistema corresponden a artículos reales verificables.",
                    "tipo_escala": "LIKERT_5"
                },
                {
                    "numero": 4,
                    "dimension_asociada": "Determinismo y Seguridad Zero-LLM",
                    "indicador": "Tasa de bloqueo de esquemas inválidos",
                    "enunciado_reactivo": "El sistema me notifica claramente si el título excede las veinte palabras o si faltan signos interrogativos.",
                    "tipo_escala": "LIKERT_5"
                },
                {
                    "numero": 5,
                    "dimension_asociada": "Arquitectura del Protocolo MCP",
                    "indicador": "Tiempo de respuesta de herramientas MCP en milisegundos",
                    "enunciado_reactivo": "La interacción con las herramientas del servidor se ejecuta con fluidez y tiempos de respuesta adecuados.",
                    "tipo_escala": "LIKERT_5"
                }
            ]
        }
    },
    "P31": {
        "step_code": "P31",
        "prompt_name": "paso_p31_guia_entrevista",
        "titulo": "P31: Guía de Entrevista en Profundidad",
        "descripcion": "Estructura una guía de preguntas abiertas y repreguntas para docentes asesores o expertos.",
        "guia_metodologica": """
Diseño de la guía de entrevista cualitativa:
1. nombre_guia: título de la guía (5 a 150 caracteres).
2. perfil_informante_clave: características de los entrevistados (10 a 200 caracteres, ej. 'Docentes asesores de tesis con más de 5 años de experiencia').
3. preguntas: lista de entre 3 y 25 preguntas.
4. Cada pregunta debe contener:
   - numero: entero del 1 al 30.
   - eje_tematico: dimensión o tema central evaluado.
   - pregunta_principal: interrogante abierta de 10 a 300 caracteres.
   - repregunta_profundizacion: pregunta secundaria para profundizar en detalles (10 a 300 caracteres).
""",
        "esquema_json_ejemplo": {
            "nombre_guia": "Guía de Entrevista Semiestructurada a Asesores Docentes de Tesis",
            "perfil_informante_clave": "Docentes universitarios asesores del área de ingeniería y jurados de tesis en UTP Piura",
            "preguntas": [
                {
                    "numero": 1,
                    "eje_tematico": "Supervisión y Carga de Revisión",
                    "pregunta_principal": "¿Cuáles son los errores metodológicos más frecuentes que observa en los borradores iniciales de tesis?",
                    "repregunta_profundizacion": "¿En qué medida estos errores se deben al uso no supervisado de herramientas de inteligencia artificial?"
                },
                {
                    "numero": 2,
                    "eje_tematico": "Trazabilidad de Citas y Alucinaciones",
                    "pregunta_principal": "¿Cómo verifica actualmente la autenticidad y existencia de las referencias citadas por los estudiantes?",
                    "repregunta_profundizacion": "¿Considera útil que el sistema bloquee automáticamente la inclusión de fuentes no registradas con PDF físico?"
                },
                {
                    "numero": 3,
                    "eje_tematico": "Flujo Colaborativo y Observaciones",
                    "pregunta_principal": "¿De qué manera impacta el uso de comentarios anclados sobre coordenadas de texto en la retroalimentación docente?",
                    "repregunta_profundizacion": "¿Facilita el control de versiones evitar que el estudiante sobreescriba cambios mientras hay revisiones abiertas?"
                }
            ]
        }
    },
    "P32": {
        "step_code": "P32",
        "prompt_name": "paso_p32_piloto_calibracion",
        "titulo": "P32: Prueba Piloto y Calibración del Instrumento",
        "descripcion": "Registra el tamaño de muestra piloto, el coeficiente de confiabilidad (Alfa/Omega) y los ajustes realizados.",
        "guia_metodologica": """
Documentación de la calibración del instrumento:
1. tamanio_muestra_piloto: número entero de participantes en la prueba piloto (entre 5 y 100).
2. coeficiente_confiabilidad_obtenido: valor decimal entre 0.0 y 1.0 (Alfa de Cronbach o Coeficiente Omega).
3. ajustes_redaccion_items: lista de 1 a 15 modificaciones realizadas a los reactivos para mejorar su claridad o discriminación.
4. estado_instrumento: debe ser 'CALIBRADO' (si supera el umbral de aceptación) o 'REQUIERE_REVISION'.
""",
        "esquema_json_ejemplo": {
            "tamanio_muestra_piloto": 15,
            "coeficiente_confiabilidad_obtenido": 0.88,
            "ajustes_redaccion_items": [
                "Se reformuló el ítem 3 para explicitar que la verificación documental se realiza contra el PDF completo del antecedente.",
                "Se ajustó la redacción del ítem 4 para diferenciar claramente entre errores de formato y restricciones de palabras."
            ],
            "estado_instrumento": "CALIBRADO"
        }
    }
}
