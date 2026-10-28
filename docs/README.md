# Documentación de TesisMCP

Esta carpeta reúne la descripción del proyecto, la arquitectura, la metodología, los antecedentes y el informe del Curso Integrador 1.

> **Estado verificado al 26/10/2026:** la referencia corta del alcance vigente es [Estado verificable del producto](./07_desarrollo_prototipo/estado_version_producto.md). Las consultas fechadas y los planes de semanas anteriores se conservan como historial y llevan una advertencia cuando describen alternativas descartadas.

## Informe

- [Informe IEEE en Markdown](./06_informe_final_curso/informe_academico_curso_integrador_IEEE.md)
- [Informe IEEE en Word](./06_informe_final_curso/informe_academico_curso_integrador_IEEE.docx)
- [Versión base del informe en Markdown](./06_informe_final_curso/informe_academico_curso_integrador.md)

El Word se genera a partir del Markdown IEEE mediante `scripts/build_informe_ieee.py`. En esta actualización se corrigieron los Markdown; el DOCX existente debe regenerarse antes de entregarlo para incorporar esos cambios. La versión base conserva APA y la edición IEEE conserva citas numéricas, sin mezclar estilos dentro de cada documento.

Para modelos y migraciones, la fuente de verdad es el [modelo de datos físico](./02_arquitectura_y_sistema/modelo_datos_fisico.md): conserva una base histórica y documenta explícitamente las extensiones posteriores, incluidos B1.1–B1.3 y B1+B2.2/B1+B2.3. El editor canónico añade dos modelos y las migraciones `0025`–`0026` incorporan su persistencia y referencia a propuestas IA aceptadas; los diagramas PNG/SVG son apoyo visual y deben contrastarse con el código y las migraciones vigentes.

## Documentación por tema

- **Para agentes que empiezan:** leer primero la [Guía Maestra para Agentes](../GUIA_AGENTE.md), luego la [visión integral y decisiones de diseño](./01_vision_y_alcance/propuesta_integral_tesismcp_y_decisiones_de_diseno.md) y el [estado verificable del producto](./07_desarrollo_prototipo/estado_version_producto.md). Mantener separadas las capacidades actuales y la dirección objetivo.
- [Visión y alcance](./01_vision_y_alcance/ficha_tecnica_proyecto.md)
- [Propuesta integral, decisiones de diseño y ruta de desarrollo](./01_vision_y_alcance/propuesta_integral_tesismcp_y_decisiones_de_diseno.md)
- [Guía maestra para agentes de IA del equipo](../GUIA_AGENTE.md)
- [Arquitectura del sistema](./02_arquitectura_y_sistema/arquitectura_global.md)
- [Guía de arquitectura y sistema "con manzanitas" (El porqué y para qué)](./02_arquitectura_y_sistema/guia_arquitectura_con_manzanitas.md)
- [Especificación para iniciar el código](./02_arquitectura_y_sistema/arquitectura_detallada_componentes.md)
- [Guía de desarrollo del backend para la versión completa](./02_arquitectura_y_sistema/guia_backend_version_completa_para_agentes.md)
- [Especificación de búsqueda, lectura documental, revisión de afirmaciones/citas y apoyos invitados](./02_arquitectura_y_sistema/especificacion_busqueda_y_revision_de_evidencia.md)
- [Paquete de especificación integral del backend](./02_arquitectura_y_sistema/especificacion_integral_backend.md)
- [Plan de entregas y definición de terminado del backend](./02_arquitectura_y_sistema/plan_entregas_backend.md)
- [Paquete B1.2: comentarios y decisiones anclados al snapshot](./02_arquitectura_y_sistema/paquete_b1_2_revision_anclada_snapshot.md)
- [Paquete B1.3: exportación DOCX congelada desde el snapshot aprobado](./02_arquitectura_y_sistema/paquete_b1_3_exportacion_congelada_snapshot.md)
- [Paquete B1+B2.1: incorporación tipada de propuestas textuales aceptadas](./02_arquitectura_y_sistema/paquete_b1_b2_1_materializacion_textual_propuestas.md)
- [Paquete B1+B2.2: documento canónico versionado por capítulo](./02_arquitectura_y_sistema/paquete_b1_b2_2_documento_canonico.md)
- [Paquete B1+B2.3: diffs IA y aceptación explícita en el documento](./02_arquitectura_y_sistema/paquete_b1_b2_3_diffs_ia_documento.md)
- [Modelo de datos físico y diccionario de tablas](./02_arquitectura_y_sistema/modelo_datos_fisico.md)
- [Referencia técnica de restricciones, índices y migraciones](./02_arquitectura_y_sistema/restricciones_indices_referencia.md)
- [Guía de implementación y aprendizaje del Servidor MCP](../mcp_server/README.md)
- [Visor interactivo de diagramas de base de datos](./02_arquitectura_y_sistema/visor_diagramas_bd.html)
- [Diagramas de base de datos en alta resolución: ER Conceptual, Lógico y Físico](./02_arquitectura_y_sistema/diagrama_modelo_fisico_completo.png)
- [Fuentes editables de diagramas (Mermaid, Draw.io, SVG)](./02_arquitectura_y_sistema/diagramas_editables/)
- [Secuencia del sistema](./02_arquitectura_y_sistema/secuencia_del_sistema.md)
- [Estructura de capítulos y prompts](./03_metodologia_y_prompts/estructura_capitulos_1_a_7.md)
- [Referencias de prompts originales (Capítulos 1 a 7)](./03_metodologia_y_prompts/referencias_prompts/)
- [Estrategia de búsqueda](./04_modulo_investigacion_y_busqueda/estrategia_busqueda_antecedentes.md)
- [Análisis de los antecedentes seleccionados](./04_modulo_investigacion_y_busqueda/analisis_profundo_antecedentes.md)
- [Índice de fuentes y PDF conservados](./antecedentes_descargados/README.md)
- [Sistema de comentarios del asesor](./05_modulo_colaborativo_asesor/sistema_comentarios_y_revision.md)
- [Prototipo interactivo](./02_arquitectura_y_sistema/prototipo_interactivo.html)
- [Contratos Pydantic y Validadores Deterministas de Dominio](./03_metodologia_y_prompts/contratos_pydantic_y_validadores_mvp.md)
- [Bitácora de desarrollo del prototipo y registro de evidencias](./07_desarrollo_prototipo/bitacora_desarrollo_y_evidencias.md)
- [Protocolo de evaluación experimental del prototipo](./07_desarrollo_prototipo/protocolo_evaluacion_experimental.md)
- [Caso semilla canónico UTP Sede Piura (JSON)](./07_desarrollo_prototipo/caso_prueba_semilla_piura.json)
- [Arquitectura del circuito cerrado determinista (Zero-LLM) y herramientas open source](./02_arquitectura_y_sistema/arquitectura_circuito_cerrado_zero_llm.md)
- [Guía maestra de división del equipo, conexión de módulos y herramientas (5 integrantes)](./07_desarrollo_prototipo/plan_trabajo_equipo_5_integrantes.md)
- [Base de conocimiento: Dudas, consultas y respuestas clasificadas](./dudas_y_consultas/README.md)

---

## 👥 Guía Directa por Rol del Equipo (Qué debe leer cada integrante)

Para que ningún integrante se pierda ni programe algo distinto a lo acordado, todos deben empezar leyendo la **[Guía Maestra del Equipo](./07_desarrollo_prototipo/plan_trabajo_equipo_5_integrantes.md)** y luego sus documentos específicos:

| Rol Elegido | Documentos Guía Obligatorios para su Rol |
| :--- | :--- |
| **🗄️ Rol 1: Base de Datos & Modelos (PostgreSQL + Django ORM)** | 1. [Modelo de datos físico y diccionario de tablas](./02_arquitectura_y_sistema/modelo_datos_fisico.md)<br/>2. [Referencia de restricciones, índices y migraciones](./02_arquitectura_y_sistema/restricciones_indices_referencia.md)<br/>3. [Visor interactivo de diagramas de BD](./02_arquitectura_y_sistema/visor_diagramas_bd.html) |
| **🤖 Rol 2: Servidor MCP & Agente IA** | 1. [Guía del Servidor MCP y puente `django_bridge.py`](../mcp_server/README.md)<br/>2. [Estructura de capítulos y pasos P01–P32](./03_metodologia_y_prompts/estructura_capitulos_1_a_7.md)<br/>3. [Secuencia del sistema](./02_arquitectura_y_sistema/secuencia_del_sistema.md) |
| **⚙️ Rol 3: Reglas de Validación & API REST (Django Ninja)** | 1. [Contratos Pydantic y servicio `steps.py`](./03_metodologia_y_prompts/contratos_pydantic_y_validadores_mvp.md)<br/>2. [Especificación detallada de componentes y endpoints](./02_arquitectura_y_sistema/arquitectura_detallada_componentes.md) |
| **🖥️ Rol 4: Panel del Asesor & Frontend (UI)** | 1. [Sistema de comentarios, revisión y código `django-unfold`](./05_modulo_colaborativo_asesor/sistema_comentarios_y_revision.md)<br/>2. [Prototipo interactivo HTML de referencia visual](./02_arquitectura_y_sistema/prototipo_interactivo.html) |
| **📋 Rol 5: Calidad (QA), Pruebas & Word** | 1. [Bitácora de desarrollo, scripts Pytest y capturas Word](./07_desarrollo_prototipo/bitacora_desarrollo_y_evidencias.md)<br/>2. [Protocolo experimental y encuesta SUS](./07_desarrollo_prototipo/protocolo_evaluacion_experimental.md)<br/>3. [Caso semilla canónico UTP Sede Piura (JSON)](./07_desarrollo_prototipo/caso_prueba_semilla_piura.json) |

Los PDF antiguos se mantienen en `antecedentes_descargados/` como material de consulta. El índice distingue cuáles integran el informe y cuáles quedaron fuera de la selección.
