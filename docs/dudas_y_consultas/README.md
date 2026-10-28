# Repositorio de Dudas, Consultas y Respuestas (Base de Conocimiento)

> **Estado respecto del producto actual (18/10/2026):** este directorio conserva consultas históricas que pueden describir alternativas descartadas. El alcance vigente usa `MCPServer` por `stdio`, API Django Ninja y panel Django Admin/Unfold para el asesor; no incluye frontend propio del tesista ni infraestructura pública seleccionada. Consulte [Estado verificable del producto](../07_desarrollo_prototipo/estado_version_producto.md).


Este directorio es el espacio exclusivo y centralizado para almacenar, organizar y dar seguimiento a todas las **dudas, consultas técnicas, metodológicas y académicas**, junto con sus **respuestas fundamentadas**.

---

## 📂 Organización por Categorías Temáticas

Los archivos Markdown (`.md`) se guardan dentro de subcarpetas clasificadas por área temática. Si surge una consulta sobre un área que aún no cuenta con subcarpeta, **se crea una nueva subcarpeta específica** inmediatamente.

| Subcarpeta | Área Temática / Enfoque |
| :--- | :--- |
| [`arquitectura_y_backend/`](./arquitectura_y_backend/) | Dudas sobre modelos de datos, PostgreSQL, Django ORM, API REST, endpoints Ninja y reglas de negocio. |
| [`servidor_mcp_e_ia/`](./servidor_mcp_e_ia/) | Consultas sobre el protocolo MCP, herramientas (`tools`), prompts de los agentes, prompts LLM y orquestación. |
| `metodologia_y_prompts/` | Pasos metodológicos P01–P32, contratos Pydantic y capítulos de tesis. La subcarpeta se creará cuando exista una consulta de esa categoría. |
| [`modulo_asesor_y_ui/`](./modulo_asesor_y_ui/) | Interfaz gráfica, panel del asesor (`django-unfold`), flujo de comentarios, observaciones y revisiones. |
| `investigacion_y_antecedentes/` | Categoría prevista para futuras consultas sobre búsqueda y grounding. |
| `general/` | Categoría prevista para futuras consultas de gestión o cronograma. |

> 💡 **Regla de escalabilidad:** Si aparece un nuevo tema (ej. `seguridad_y_auth/`, `despliegue_docker/`, `analisis_estadistico/`), se crea su subcarpeta correspondiente y se registra en esta tabla.

---

## 📝 Estándar de Nombre de Archivo

Para mantener un orden cronológico y temático rastreable:
- Formato: `YYYY-MM-DD_<tema_o_resumen_pregunta_en_slug>.md`
- Ejemplo: `2026-10-17_validacion_pydantic_vs_django_orm.md`

---

## 📋 Plantilla Estándar para Cada Consulta (`template`)

Todo nuevo archivo de consulta debe contener la siguiente estructura:

```markdown
# [Tema / Pregunta en Título Claro]

- **Fecha:** YYYY-MM-DD
- **Categoría:** [Nombre de la subcarpeta]
- **Estado:** [Resuelta / En revisión / Pendiente]
- **Participante / Rol:** [Ej. Estudiante, Asesor, Rol 1, etc.]

---

## ❓ 1. Pregunta o Duda Planteada
[Descripción exacta y detallada de la duda o consulta.]

## 💡 2. Respuesta Fundamentada
[Explicación clara, técnica y rigurosa de la solución o respuesta, con justificación conceptual y técnica.]

## 🛠️ 3. Código o Ejemplo Práctico (si aplica)
[Snippets de código, contratos o configuraciones relevantes.]

## 🔗 4. Referencias y Archivos Vinculados
- Ruta o enlace real del documento de referencia.
- Cita o fuente documental primaria (si aplica).
```

---

## 🗂️ Registro Maestro de Consultas

| ID | Fecha | Subcarpeta | Pregunta / Título | Estado |
| :---: | :---: | :--- | :--- | :---: |
| **001** | 2026-10-17 | [`servidor_mcp_e_ia/`](./servidor_mcp_e_ia/) | [Guía Maestra: Todo sobre MCP (Fundamentos, Arquitectura, SDK e Integración)](./servidor_mcp_e_ia/2026-10-17_guia_completa_aprendizaje_mcp.md) | Resuelta |
| **002** | 2026-10-17 | [`servidor_mcp_e_ia/`](./servidor_mcp_e_ia/) | [¿Por qué usar stdio si iremos a la nube? Flujo entre Web, IA y MCP](./servidor_mcp_e_ia/2026-10-17_stdio_vs_sse_despliegue_nube.md) | Resuelta |
| **003** | 2026-10-17 | [`modulo_asesor_y_ui/`](./modulo_asesor_y_ui/) | [Conector de Agente Personal en el Panel Derecho (Evitar cambio de ventanas)](./modulo_asesor_y_ui/2026-10-17_conector_agente_panel_derecho.md) | Resuelta |
| **004** | 2026-10-17 | [`modulo_asesor_y_ui/`](./modulo_asesor_y_ui/) | [Evaluación Imparcial: Opciones de UI, Sincronización y Modelo de Negocio](./modulo_asesor_y_ui/2026-10-17_evaluacion_imparcial_opciones_copilot_y_modelo_negocio.md) | Resuelta |
| **005** | 2026-10-17 | [`arquitectura_y_backend/`](./arquitectura_y_backend/) | [Investigación de Herramientas Open-Source: Wordcraft, TipTap, Novel.so y n8n](./arquitectura_y_backend/2026-10-17_herramientas_opensource_tiptap_wordcraft_n8n.md) | Resuelta |
| **006** | 2026-10-17 | [`servidor_mcp_e_ia/`](./servidor_mcp_e_ia/) | [Análisis Técnico de storytold/wordcraft: Word en Rust con Servidor MCP Nativo](./servidor_mcp_e_ia/2026-10-17_storytold_wordcraft_integracion_mcp.md) | Resuelta |
| **007** | 2026-10-17 | [`modulo_asesor_y_ui/`](./modulo_asesor_y_ui/) | [Viabilidad de Reutilizar el Frontend: Canvas Rust/Wasm vs. DOM Web (TipTap/Novel)](./modulo_asesor_y_ui/2026-10-17_viabilidad_frontend_wordcraft_vs_dom_tiptap.md) | Resuelta |
| **008** | 2026-10-17 | [`servidor_mcp_e_ia/`](./servidor_mcp_e_ia/) | [Arquitectura Multi-MCP: ¿Unificar herramientas de WordCraft o tener servidores separados?](./servidor_mcp_e_ia/2026-10-17_arquitectura_multi_mcp_vs_unificado.md) | Resuelta |
| **009** | 2026-10-17 | [`modulo_asesor_y_ui/`](./modulo_asesor_y_ui/) | [Investigación Técnica: ¿Existe novel.so? Análisis de novel.sh y el paquete npm 'novel'](./modulo_asesor_y_ui/2026-10-17_investigacion_novel_sh_vs_novel_so.md) | Resuelta |
| **010** | 2026-10-17 | [`modulo_asesor_y_ui/`](./modulo_asesor_y_ui/) | [Investigación y Análisis Crítico: ¿Qué es pensiv.so y qué alternativas Open-Source existen para TesisMCP?](./modulo_asesor_y_ui/2026-10-17_alternativas_opensource_pensiv_so.md) | Resuelta |
| **011** | 2026-10-17 | [`modulo_asesor_y_ui/`](./modulo_asesor_y_ui/) | [Decisión de Arquitectura Frontend: Selección Tecnológica y Diseño de la Interfaz de TesisMCP](./modulo_asesor_y_ui/2026-10-17_seleccion_tecnologica_y_diseno_frontend_tesismcp.md) | Resuelta |
| **012** | 2026-10-17 | [`modulo_asesor_y_ui/`](./modulo_asesor_y_ui/) | [Maqueta de Interfaz DOCX / Word para TesisMCP (Layout de 3 Paneles)](./modulo_asesor_y_ui/2026-10-17_maqueta_interfaz_word_docx_tesismcp.md) | Resuelta |
| **013** | 2026-10-17 | [`modulo_asesor_y_ui/`](./modulo_asesor_y_ui/) | [Paradigma Híbrido: Jenni AI + NotebookLM + Word/Docs en TesisMCP](./modulo_asesor_y_ui/2026-10-17_paradigma_hibrido_jenni_ai_notebooklm_word.md) | Resuelta |
| **014** | 2026-10-22 | [`general/`](./general/) | [Análisis neutral de la reunión con el asesor A](./general/2026-10-22_analisis_reunion_asesor_a.md) | En revisión |
| **015** | 2026-10-22 | [`general/`](./general/) | [Análisis neutral de la demostración del producto esperado](./general/2026-10-22_analisis_demostracion_producto_esperado.md) | En revisión |
| **016** | 2026-10-22 | [`general/`](./general/) | [Análisis neutral de la conversación con el profesor invitado](./general/2026-10-22_analisis_profesor_invitado_y_ruta_metodologica.md) | En revisión |
| **017** | 2026-10-22 | [`general/`](./general/) | [Síntesis consolidada de las reuniones sobre TesisMCP](./general/2026-10-22_sintesis_consolidada_reuniones_tesismcp.md) | En revisión |









