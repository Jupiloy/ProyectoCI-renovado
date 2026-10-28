# Conector de Agente Personal en el Panel Derecho (Evitar el cambio de ventanas)

> **Estado respecto del producto actual (18/10/2026):** esta es una consulta histórica y puede describir alternativas descartadas. El alcance vigente usa `MCPServer` por `stdio`, API Django Ninja y panel Django Admin/Unfold para el asesor; no incluye frontend propio del tesista ni infraestructura pública seleccionada. Consulte [Estado verificable del producto](../../07_desarrollo_prototipo/estado_version_producto.md).


- **Fecha:** 2026-10-17
- **Categoría:** `modulo_asesor_y_ui`
- **Estado:** Resuelta / Propuesta de Diseño Aprobada
- **Participante / Rol:** Estudiante / Equipo TesisMCP (Roles 2 y 4: Servidor MCP y Frontend/UI)

---

## ❓ 1. Pregunta o Duda Planteada

> **"¿Es posible que en la columna derecha hagamos como un 'conector' a la IA o agente del propio usuario?**  
> En el modelo de la web:
> - A la **izquierda**: Fuentes y documentación (estilo NotebookLM / RAG).
> - Al **centro**: El documento en vivo tipo Word / Google Docs (lienzo A4 donde se redacta el informe).
> - A la **derecha**: Sugerencias, historial y observaciones del asesor.  
> 
> ¿Podemos agregarle en el lado derecho una ventanita/conector para usar nuestro propio agente (por ejemplo, **Antigravity**) sin necesidad de estar cambiando de ventana entre aplicaciones (Alt+Tab) a cada rato para ver cómo va quedando el resultado?"

---

## 💡 2. Respuesta Fundamentada y Viabilidad Técnica

### **Sí, es 100% posible y es una excelente decisión de experiencia de usuario (UX).**

El problema que planteas se conoce en ingeniería de software e interacción humano-computadora como **"Fatiga por cambio de contexto" (*Context-Switching Friction*)**. Si redactas en el chat de tu agente (Antigravity/Cursor/Claude) y tienes que cambiarte a Chrome a cada minuto para ver si el documento se actualizó, la experiencia se vuelve lenta e incómoda.

Para solucionar esto de raíz, existen **tres enfoques técnicos perfectamente viables y complementarios**:

---

### Enfoque A: "Copilot Web Integrado con Conector Personal" (Dentro de la Página Web)

En el diseño de 3 columnas de la web de TesisMCP, el panel derecho puede incorporar un selector de pestañas:

```text
+----------------------+----------------------------------+-----------------------------+
|   COLUMNA IZQUIERDA  |         COLUMNA CENTRAL          |       COLUMNA DERECHA       |
|                      |                                  |                             |
|  📚 Fuentes & RAG    |    📄 Lienzo A4 (Google Docs)    |  [ Observaciones | Mi Agente ]
|                      |                                  |  ---------------------------|
|  • paper_iot.pdf     |  Capítulo I: Introducción        |  🤖 Chat con Agente (MCP)   |
|  • directiva_utp.pdf |                                  |  > Usuario:                 |
|  • [Subir nueva...]  |  1.1 Realidad Problemática...    |    "Redacta el paso P04 con |
|                      |  [Texto actualizado en vivo]     |    los papers de la izq."   |
|                      |                                  |  > Agente:                  |
|                      |                                  |    "Generando título..."    |
|                      |                                  |  [ Aplicar al Documento ]   |
+----------------------+----------------------------------+-----------------------------+
```

#### ¿Cómo funciona técnicamente?
1. **Pestaña "Mi Agente":** Un componente de chat web que se comunica mediante WebSockets o SSE con el backend de Django Ninja.
2. **Bring Your Own Agent (BYOA):** En la configuración de usuario, el tesista puede elegir:
   - **Agente del Sistema:** Usa el modelo por defecto provisto por la plataforma.
   - **Agente Personal / Propia API Key:** El tesista ingresa su clave (Claude, Gemini, OpenAI) o la URL de su propio servidor de agentes local (ej. endpoint local de Antigravity).
3. **Acción "Insertar en Documento":** Cuando el agente responde en el chat de la derecha, aparece un botón interactivo *`[Aplicar al Documento]`*. Al hacer clic, el texto se inyecta directamente en el editor TipTap central sin salir del navegador.

---

### Enfoque B: "El Camino Inverso: El Documento dentro de Antigravity" (Panel Webview Sidecar)

Dado que usas **Antigravity**, existe una alternativa aún más directa sin salir de tu entorno de desarrollo:

Antigravity soporta **Webviews integradas** (paneles web interactivos dentro del mismo editor).
1. En el panel izquierdo/central de Antigravity tienes tu espacio de trabajo y la vista web del documento en vivo (`http://localhost:8000` o visor HTML local).
2. En el panel derecho de Antigravity tienes tu chat de agente con las herramientas MCP conectadas.
3. Le pides al agente: *"Antigravity, redacta el paso P04 utilizando las fuentes indexadas"*.
4. Antigravity ejecuta la herramienta MCP `guardar_borrador`.
5. La base de datos se actualiza y **el visor web embebido en la pestaña de al lado se refresca automáticamente**.
6. **Resultado:** Trabajas en una sola pantalla, con tu editor, tus archivos, tu agente y el documento visualizándose en paralelo.

---

### Enfoque C: "Sincronización en Tiempo Real por WebSockets (Live Reload)"

Si prefieres tener Antigravity en una mitad del monitor y el navegador Chrome en la otra mitad:
- La aplicación web de TesisMCP mantendrá una conexión **WebSocket activa** (`ws://localhost:8000/ws/thesis/{project_id}/`).
- Cuando le pidas a Antigravity en su terminal o chat que genere un paso, Antigravity invocará el MCP por `stdio`.
- El servidor MCP guarda la versión en PostgreSQL.
- Django emite un evento por WebSocket al navegador.
- **El lienzo central de Chrome se actualiza al instante en milisegundos**, sin necesidad de que hagas Alt+Tab ni de que presiones F5 para refrescar.

---

## 🛠️ 3. Hoja de Ruta de Implementación en el Proyecto

| Fase | Funcionalidad UI | Responsable |
| :--- | :--- | :--- |
| **Semana 12 (MVP)** | Panel derecho en `django-unfold` con visor de sugerencias e historial de revisiones. Vista previa en vivo del documento Markdown. | Rol 4 (Frontend/Admin) |
| **Semana 13–14** | Pestaña de Chat con el Agente en la columna derecha de la web (Web Copilot) conectada a las herramientas MCP. | Rol 2 (MCP) y Rol 4 (UI) |
| **Semana 15** | Soporte de WebSockets para Live Reload automático y panel webview para entornos de desarrollo. | Rol 3 (API Ninja) y Rol 4 |

---

## 🔗 4. Referencias y Archivos Vinculados

- [Prototipo Interactivo de la Interfaz Web (3 Columnas)](../../02_arquitectura_y_sistema/prototipo_interactivo.html)
- [Sistema de Comentarios y Lienzo Central TipTap](../../05_modulo_colaborativo_asesor/sistema_comentarios_y_revision.md)
- [Plan de Trabajo del Equipo (Rol 4: Frontend y UI)](../../07_desarrollo_prototipo/plan_trabajo_equipo_5_integrantes.md)
