# Paquete de especificación integral del backend de TesisMCP

**Estado:** guía de trabajo para completar el backend objetivo. **Actualizado:** 25/10/2026.

Este paquete convierte la dirección de producto en una base de programación para agentes. Separa lo comprobado en código de lo que falta y de las decisiones aún abiertas. No declara terminada la especificación de cada regla académica: cuando un requisito depende de la guía UTP, del asesor o de permisos externos, lo marca como pendiente de confirmación.

## Cómo usar este paquete

**Prioridad de interpretación para Argon y Flash:** `AGENTS.md` fija reglas de trabajo y verificación; el código, migraciones y pruebas vigentes prueban lo implementado; las normas UTP originales con versión/ámbito prueban requisitos institucionales; el [criterio de backend listo para frontend](./criterio_backend_listo_para_frontend.md) fija el alcance objetivo; el [plan de entregas](./plan_entregas_backend.md) fija el orden de construcción; los contratos específicos desarrollan cada dominio. El [estado de producto](../07_desarrollo_prototipo/estado_version_producto.md) describe su **fecha de corte**, no garantiza el estado del código de hoy. La documentación del MVP, transcripciones y prompts originales son antecedentes, no órdenes de reconstruir el backend ni límites del producto final. Si dos fuentes del mismo nivel discrepan, inspeccionar el código/fuente primaria y registrar la decisión; no escoger la frase más conveniente.

Antes de programar, leer en este orden:

1. [AGENTS.md](../../AGENTS.md) y [Guía Maestra para Agentes](../../GUIA_AGENTE.md).
2. [Visión integral y decisiones de producto](../01_vision_y_alcance/propuesta_integral_tesismcp_y_decisiones_de_diseno.md).
3. [Estado verificable del producto](../07_desarrollo_prototipo/estado_version_producto.md) y [README del backend](../../backend/README.md).
4. Este paquete:
   - [Guía de desarrollo del backend](./guia_backend_version_completa_para_agentes.md).
   - [Inventario de capacidades y brechas](./inventario_brechas_backend.md).
   - [Contratos de dominio](./contratos_dominio_backend.md).
   - [Contratos de API](./contratos_api_backend.md).
   - [Cuentas, autenticación y matriz de permisos](./matriz_permisos_y_cuentas_backend.md).
   - [Seguridad, datos y operación](./seguridad_datos_operacion_backend.md).
   - [Plan de entregas y definición de terminado](./plan_entregas_backend.md).
   - [Contrato de recorrido y prompts configurables](./contrato_recorrido_y_prompts_configurables.md), primera entrega vertical priorizada tras B0.
   - [Criterio de backend listo para frontend](./criterio_backend_listo_para_frontend.md), recorrido integral y barrera de cierre del backend objetivo.
   - [Propuesta de orden metodológico revisado](../03_metodologia_y_prompts/propuesta_orden_metodologico_revisado.md), orden inicial editable y ramas; no es un grafo ejecutable ya aprobado.
   - [Registro de decisiones abiertas y defaults recomendados](./registro_decisiones_backend.md).
   - [Especificación de búsqueda, lectura documental y revisión de afirmaciones](./especificacion_busqueda_y_revision_de_evidencia.md), requisito funcional para búsqueda asistida, importación manual de Scopus/WoS, biblioteca de documentos, auditoría afirmación–cita y apoyos invitados.
   - [Arquitectura BYOA, API y MCP](./arquitectura_byoa_api_mcp.md), que define cómo la web despacha tareas al agente del usuario, cómo el agente consulta herramientas por MCP y qué falta para nube.
   - [Primera versión de revisión inteligente de citas](./plan_revision_inteligente_citas.md), contrato propuesto para una evaluación del agente guardada como propuesta y separada de la decisión humana.
5. Para detalles ya existentes, consultar el [modelo físico](./modelo_datos_fisico.md), la [especificación arquitectónica](./arquitectura_detallada_componentes.md), la [secuencia](./secuencia_del_sistema.md), los [contratos P01–P32](../03_metodologia_y_prompts/contratos_pydantic_y_validadores_mvp.md), la [estructura de capítulos](../03_metodologia_y_prompts/estructura_capitulos_1_a_7.md) y el [flujo de revisión](../05_modulo_colaborativo_asesor/sistema_comentarios_y_revision.md).

## Alcance objetivo

El backend debe preservar P01–P32 y los capítulos 1–7 existentes y evolucionar hacia un recorrido configurable por proyecto que acompañe la tesis hasta análisis de datos reales, resultados, discusión, conclusiones y entrega. El alcance completo es objetivo de producto, no estado actual; se construye en entregas verticales. La primera entrega priorizada es el [contrato de recorrido y prompts configurables](./contrato_recorrido_y_prompts_configurables.md). No reiniciar ni reimplementar un dominio antes de comprobar el código.

El tesista y el asesor son los actores principales. El mismo asesor puede asumir funciones temáticas y metodológicas. Expertos y bibliotecarios pueden recibir invitaciones acotadas a tareas y materiales; la administración institucional mantiene configuración/guías fuera del flujo privado de cada tesis; proveedores, Zotero y n8n son conectores/capacidades opcionales. No añadir roles globales obligatorios por esas categorías. WhatsApp queda fuera. En el flujo BYOA, la web inicia jobs por la API; el conector local Antigravity reclama y entrega los jobs al runtime; el agente usa MCP para herramientas/datos con permisos del proyecto. El backend implementa conexión revocable, despacho, leases, eventos y validación de resultados. La gestión visual de conexiones/generación y la ejecución real de Antigravity aún no se han comprobado. Ver [arquitectura BYOA, API y MCP](./arquitectura_byoa_api_mcp.md) y el [contrato del conector](./contrato_conector_byoa.md).

La búsqueda asistida en Scopus/WoS debe funcionar sin API: la plataforma prepara y registra una ecuación, abre la base oficial y procesa la exportación del usuario. Un conector API es opcional y no bloquea descubrimiento abierto, búsqueda manual, importación ni consulta de documentos. La revisión de una cita debe evaluar por separado la identidad de la referencia y si pasajes inspeccionados respaldan la afirmación; sus resultados automáticos son propuestas, no aprobaciones.

## Vocabulario de certeza

- **IMPLEMENTADO:** existe en código y fue observado en el corte indicado. No implica que satisfaga toda la visión futura.
- **PARCIAL:** existe una parte, pero queda una brecha funcional o técnica descrita.
- **PENDIENTE:** no se observó implementado en el corte revisado.
- **DEPENDIENTE DE PERMISO:** requiere autorización/licencia/acceso externo comprobado.
- **DECISIÓN ABIERTA:** hay alternativas válidas sin decisión confirmada.

La documentación y el código tienen fechas de corte diferentes. Ante discrepancia, inspeccionar el código, migraciones y pruebas vigentes; actualizar este paquete con la evidencia de ese corte antes de afirmar un estado nuevo.

## Regla para convertir este paquete en código

Cada cambio debe vincularse a un requisito, un servicio/modelo/ruta existente o a la razón para añadir uno, un contrato de entrada/salida, una regla de autorización, errores esperados, migración compatible y criterio de aceptación comprobable. No usar esta especificación para inventar políticas institucionales ni permisos de Scopus/WoS/Zotero. Las salidas de IA son propuestas, no mutaciones canónicas hasta que el usuario autorizado las acepte.

El agente puede empezar de inmediato con la auditoría B0 del [plan de entregas](./plan_entregas_backend.md). Para un dominio posterior, primero completa o confirma sus decisiones de bloqueo y contratos; no necesita esperar a que estén cerradas decisiones irrelevantes para esa entrega.
