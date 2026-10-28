# Contratos Pydantic y validadores deterministas P01–P32

> **Estado verificado al 18/10/2026.** La fuente ejecutable es `backend/thesis/services/step_contracts.py`. Todos los contratos usan `extra='forbid'` y sus ejemplos MCP se validan en la suite.

## Flujo real de guardado

1. `thesis.services.access.require_project` valida al titular.
2. `thesis.services.steps.save_step` comprueba código, capítulo, UUID de idempotencia, tamaño del contenido, versión y prerrequisito.
3. El contrato de `CONTRACTS[step_code]` valida forma, rangos y validadores cruzados.
4. `step_materializers/` aplica reglas que dependen de otros pasos o de la base.
5. Una transacción actualiza el avance, crea `ChapterRevision` e incrementa `lock_version`.

## Catálogo de salidas

| Paso | Capítulo | Nombre | Campos de salida de primer nivel |
| :---: | :---: | :--- | :--- |
| P01 | 1 | Mapa de temas viables | `temas_propuestos`, `tema_preseleccionado_id` |
| P02 | 1 | Matriz de factibilidad | `matriz_comparativa`, `tema_ganador_id`, `tema_ganador_titulo` |
| P03 | 1 | Alineación ODS y relevancia | `ods_principal_numero`, `ods_principal_nombre`, `meta_ods_especifica`, `argumento_alineacion`, `linea_utp_vinculada` |
| P04 | 1 | Delimitación final y título | `titulo_oficial`, `conteo_palabras`, `variables_confirmadas`, `unidad_analisis_confirmada`, `lugar_confirmado`, `periodo_confirmado` |
| P05 | 1 | Redacción de la Introducción | `contenido_markdown`, `num_parrafos`, `palabras_totales` |
| P06 | 2 | Árbol del problema y formulación | `problema_central`, `causas_directas`, `efectos_directos`, `pregunta_general`, `preguntas_especificas` |
| P07 | 2 | Justificación de la investigación | `justificaciones`, `resumen_ejecutivo` |
| P08 | 2 | Originalidad y aporte | `brecha_detectada`, `aporte_propuesto`, `estado_evidencia` |
| P09 | 3 | Objetivos de investigación (SMART) | `objetivo_general`, `objetivos_especificos` |
| P10 | 3 | Preguntas de investigación alineadas | `pregunta_general`, `preguntas_especificas` |
| P11 | 3 | Hipótesis y variables | `tipo_investigacion`, `hipotesis_general`, `hipotesis_especificas`, `variable_independiente`, `variable_dependiente` |
| P12 | 3 | Matriz de operacionalización | `matriz_operacionalizacion` |
| P13 | 4 | Ecuaciones de búsqueda académica | `ecuacion_scopus`, `ecuacion_ieee`, `palabras_clave_es`, `palabras_clave_en` |
| P14 | 4 | Criterios de inclusión y exclusión | `criterios_inclusion`, `criterios_exclusion`, `anio_inicio`, `anio_fin`, `idiomas_admitidos` |
| P15 | 4 | Protocolo de cribado PRISMA | `registros_identificados`, `registros_duplicados_removidos`, `registros_cribados`, `articulos_evaluados_texto_completo`, `estudios_incluidos` |
| P16 | 4 | Matriz de literatura científica | `estudios` |
| P17 | 4 | Síntesis temática y patrones | `ejes_tematicos`, `consensos_literatura`, `discrepancias_o_debates` |
| P18 | 4 | Brecha y agenda de investigación | `vacio_conocimiento_identificado`, `justificacion_necesidad_estudio` |
| P19 | 4 | Redacción del marco de antecedentes | `antecedentes_internacionales`, `antecedentes_nacionales`, `sintesis_comparativa` |
| P20 | 4 | Citas y referencias normalizadas | `estilo_citacion`, `referencias_formateadas` |
| P21 | 5 | Selección de teorías base | `teorias` |
| P22 | 5 | Definiciones y constructos | `constructos` |
| P23 | 5 | Modelo conceptual y relacional | `descripcion_relaciones`, `diagrama_mermaid` |
| P24 | 5 | Proposiciones derivadas | `proposiciones_teoricas` |
| P25 | 6 | Enfoque y diseño metodológico | `enfoque`, `diseno`, `nivel_alcance`, `corte_temporal`, `justificacion_diseno` |
| P26 | 6 | Técnicas e instrumentos previstos | `tecnicas_seleccionadas`, `instrumentos_previstos`, `procedimiento_recoleccion` |
| P27 | 6 | Validez y confiabilidad | `validez_instrumento`, `confiabilidad_metodo`, `criterio_aceptabilidad` |
| P28 | 6 | Aspectos éticos y consentimiento | `consentimiento_informado_requerido`, `principios_eticos_aplicados`, `politica_confidencialidad_datos` |
| P29 | 6 | Redacción del capítulo metodológico | `contenido_markdown`, `palabras_totales` |
| P30 | 7 | Cuestionario cuantitativo | `nombre_instrumento`, `poblacion_objetivo`, `banco_items` |
| P31 | 7 | Guía de entrevista en profundidad | `nombre_guia`, `perfil_informante_clave`, `preguntas` |
| P32 | 7 | Prueba piloto y calibración | `tamanio_muestra_piloto`, `coeficiente_confiabilidad_obtenido`, `ajustes_redaccion_items`, `estado_instrumento` |

## Reglas cruzadas destacadas

- **P01–P04:** identificadores coherentes, ganador presente y puntaje correcto; el título declara y contiene sus componentes, y su conteo debe coincidir.
- **P05:** número de párrafos y palabras calculado desde el contenido.
- **P06/P10:** preguntas con signos de apertura y cierre.
- **P07:** exactamente las cuatro dimensiones exigidas.
- **P09:** objetivos iniciados por un verbo admitido de Bloom.
- **P12/P30:** estructura de variables, dimensiones, indicadores e ítems; el materializador enlaza los indicadores reales del proyecto.
- **P14/P15:** rango temporal válido y embudo PRISMA no creciente.
- **P16:** número de estudios igual a P15, años dentro de P14 y tres citas literales de una fuente `TEXT_CHECKED` con PDF, hash, páginas y extractos. El nivel resultante es `TEXT_EXTRACTED_WITH_QUOTES`.
- **P20:** admite `IEEE` y `APA_7` (compatibilidad histórica), con cantidad de referencias no menor que los estudios de P16. La validación no comprueba el formato ni la correspondencia de cada referencia.
- **P22:** los constructos deben cubrir las variables persistidas.
- **P25–P29:** consistencia de enfoque y recuentos declarados según cada contrato.
- **P32:** rango del coeficiente y tamaño piloto; no se recalcula el coeficiente desde datos crudos.

## Códigos de error relevantes

| Código | Motivo |
| :--- | :--- |
| `VALIDATION_SCHEMA_ERROR` | La salida no cumple el contrato Pydantic. |
| `PREREQUISITE_LOCKED` | Falta el paso anterior o el capítulo no está completo. |
| `VERSION_CONFLICT` | `lock_version`, estado o idempotencia no coinciden. |
| `UNVERIFIED_SOURCE` | P16 no encuentra archivo, extracción o cita literal válida. |
| `SOURCE_METADATA_MISMATCH` | Título, año, DOI o páginas contradicen la ficha registrada. |
| `RULE_CONSISTENCY_MISMATCH` | La salida contradice pasos previos o entidades canónicas. |

## Límites de la validación

Los contratos comprueban estructura y varias relaciones deterministas. No demuestran verdad científica, calidad argumentativa, revisión por pares ni procedencia real de un coeficiente estadístico. Esas decisiones requieren evidencia documental y revisión humana.

## Pruebas relacionadas

- `backend/thesis/tests/test_extended_steps.py` y `extended_steps/`: flujo P01–P32.
- `test_academic_flow.py`: idempotencia, revisión y P20.
- `test_sources.py`: conteo físico y extracción.
- `test_mcp_prompts.py`: ejemplos de los 32 prompts contra contratos.
