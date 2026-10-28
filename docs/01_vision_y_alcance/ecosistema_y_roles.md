# Ecosistema y Roles de la Plataforma

> **Estado verificado al 18/10/2026:** la interfaz web disponible es el panel Django Admin/Unfold del asesor. El tesista opera mediante MCP o API; las funciones institucionales y una web propia del tesista son posibilidades futuras.

## 1. Visión del Producto
El sistema se concibe como un **"NotebookLM metodológico y colaborativo para tesis e investigación científica"**. A diferencia de los blocs de notas genéricos de IA, esta plataforma combina:
1. **RAG Grounded:** La IA se alimenta de las fuentes reales que el estudiante recopila.
2. **Dirección Metodológica:** Una máquina de estados estricta que no permite dar pasos en falso.
3. **Supervisión Asíncrona:** Un entorno compartido donde el asesor de tesis acompaña el proceso sin burocracia.

---

## 2. Definición de Roles en el Sistema

### 2.1 El Tesista (Acompañamiento Escalonado por Pasos)
* **Perfil:** Estudiante de pregrado enfrentando el desafío de la hoja en blanco y la formulación metodológica.
* **Propuesta de Valor:** La plataforma actúa como un **tutor metodológico interactivo paso a paso** (vía Servidor MCP en su cliente de IA: Cursor o Claude Desktop).
* **Mecanismo Preventivo (*Poka-Yoke*):**
  * El sistema le impide dar pasos en falso: no le permite redactar la introducción si no ha delimitado el título a 20 palabras; no le permite formular objetivos si no tiene un árbol de problemas coherente.
  * Mantiene la memoria persistente del proyecto (`research_profile`, `consistency_row`), evitando que la IA sufra de amnesia o alucine variables distintas en turnos posteriores.
  * Es una herramienta **constructiva, interactiva y preventiva**.

### 2.2 El Asesor de Tesis (Circuito Cerrado de Auditoría y Dictamen Zero-LLM)
* **Perfil:** Docente investigador con sobrecarga de trabajo y múltiples tesistas asignados.
* **Propuesta de valor:** La plataforma presenta al asesor revisiones, observaciones y comprobaciones deterministas en Django Admin/Unfold. El ahorro de tiempo todavía no se ha medido con asesores reales.
* **Mecanismo de Circuito Cerrado (Zero-LLM):**
  * **Validación sin LLM en el backend:** Los contratos y servicios comprueban reglas concretas, procedencia de fuentes y rangos. Un registro DOI o una coincidencia textual no demuestran por sí solos la validez científica.
  * **Panel de control:** El asesor consulta capítulos, revisiones y comentarios. Las métricas institucionales agregadas todavía no están implementadas.
  * **Decisión Académica:** Con el trabajo mecánico ya auditado por el circuito cerrado, el asesor dedica su tiempo a la retroalimentación cualitativa y al dictamen oficial (`CHANGES_REQUESTED` o `APPROVED`).

### 2.3 La Coordinación Académica / Universidad (Opcional - Vista Institucional)
* **Métricas y Gobernanza:**
  * Monitoreo de tasas de avance de titulación por carrera o facultad.
  * Identificación de "cuellos de botella" (por ejemplo, detectar si el 60% de alumnos se estanca en el Capítulo 4).
  * Reportes de alineamiento de tesis con los Objetivos de Desarrollo Sostenible (ODS).

Esta vista institucional es una posibilidad posterior: el [modelo físico actual](../02_arquitectura_y_sistema/modelo_datos_fisico.md) define tesista y asesor por proyecto, pero todavía no incluye permisos ni tablas de agregación para Coordinación Académica.

### 2.4 Relación entre roles y datos

`project_participant` registra al titular y al asesor activos. `research_profile` y `consistency_row` conservan el contexto metodológico; `step_progress` indica el avance; `chapter_revision`, `review_comment` y `review_event` preservan el historial de redacción y revisión. Las fuentes y citas verificables se incorporan con `source_document`, `source_excerpt` y `evidence_link`. Estas entidades ya están implementadas. Ningún rol ni cliente de IA obtiene permisos por declarar un `user_id` en la petición.

---

## 3. Matriz Comparativa: Solución vs. Alternativas Actuales

| Característica | ChatGPT / Claude Base | NotebookLM (Google) | Plantillas / Acosta Research | **Nuestra Plataforma TesisMCP** |
| :--- | :---: | :---: | :---: | :---: |
| **Estructura Metodológica (Cap. 1 al 7)** | ❌ No (Chat libre) | ❌ No (Bloc de notas) | ⚠️ Manual (Copiar/pegar) | **✅ Automatizada por MCP** |
| **Memoria de Variables Persistente** | ❌ Se olvida en chats largos | ❌ Parcial | ❌ Ninguna | **Diseño: perfil y matriz aislados por proyecto** |
| **Trazabilidad Bibliográfica** | ⚠️ Requiere verificación externa | ⚠️ Depende de las fuentes disponibles | ⚠️ Revisión manual | **Diseño: fuente → extracto → afirmación, sujeto a verificación** |
| **Panel para el Asesor de Tesis** | ❌ Inexistente | ❌ Solo compartir notas | ❌ Inexistente | **Panel Django Admin/Unfold con comentarios anclados** |
| **Resolución de observaciones** | ❌ Manual | ❌ Manual | ❌ Manual | **Nueva revisión del tesista y resolución registrada; no hay subsanación automática en un clic** |
| **Contrato de citación APA 7ª** | ⚠️ Impreciso | ❌ No audita | ⚠️ Inconsistente | **Validación estructural en P20; formato de referencias pendiente de revisión humana** |
