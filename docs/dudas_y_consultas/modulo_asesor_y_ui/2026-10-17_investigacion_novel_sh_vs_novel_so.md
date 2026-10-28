# Investigación Técnica: ¿Existe novel.so? Análisis de novel.sh y el paquete npm 'novel'

> **Estado respecto del producto actual (18/10/2026):** esta es una consulta histórica y puede describir alternativas descartadas. El alcance vigente usa `MCPServer` por `stdio`, API Django Ninja y panel Django Admin/Unfold para el asesor; no incluye frontend propio del tesista ni infraestructura pública seleccionada. Consulte [Estado verificable del producto](../../07_desarrollo_prototipo/estado_version_producto.md).


- **Fecha:** 2026-10-17
- **Categoría:** `modulo_asesor_y_ui`
- **Estado:** Resuelta / Verificada con Navegador
- **Participante / Rol:** Estudiante / Equipo TesisMCP (Rol 4: Frontend y UI)

---

## ❓ 1. Pregunta o Duda Planteada

> **"¿Puedes buscar si `novel.so` existe? Si me gusta, podemos ir por esa herramienta."**

Se ejecutó una investigación web completa con el agente de navegación para verificar:
1. Si el dominio `novel.so` existe o si el proyecto utiliza otro dominio oficial.
2. El estado actual de la demo interactiva en vivo, su repositorio oficial y documentación.
3. El paquete oficial de npm (`novel`), sus componentes (menú flotante, *slash commands*, autocompletado IA) y dependencias.
4. Su viabilidad técnica para implementarlo en **TesisMCP**.

---

## 💡 2. Resultados de la Inspección en Vivo

### 2.1. El Dominio: Confusión entre `novel.so` y `novel.sh`

* **¿Existe `novel.so`?:** **NO** pertenece a este proyecto.  
  Al ingresar a `https://novel.so`, el servidor redirige de inmediato a **`https://pensiv.so/en`** (una plataforma comercial privada de escritura creativa llamada *Pensiv*).
* **El Dominio Oficial Real:** **[`https://novel.sh`](https://novel.sh)**
* **Documentación Oficial:** **[`https://novel.sh/docs/introduction`](https://novel.sh/docs/introduction)** (alojada en Mintlify).
* **Repositorio en GitHub:** **[`https://github.com/steven-tey/novel`](https://github.com/steven-tey/novel)** (creado por Steven Tey, con más de 16,400 estrellas y licencia abierta **Apache-2.0**).

---

### 2.2. Estado de la Demo Pública en `novel.sh`
* Al navegar a la raíz de `novel.sh`, la demo pública en Vercel presentó un error de cliente (`Application error: TypeError: n is not iterable`) debido a una advertencia interna de TipTap con extensiones duplicadas (`image` y `codeBlock`).
* Sin embargo, la **documentación (`novel.sh/docs`) y el código fuente en GitHub están 100% operativos, actualizados y documentados**, mostrando la estructura exacta de sus componentes.

---

### 2.3. El Paquete NPM (`npm i novel`) y su Arquitectura

Novel publica el paquete oficial **`novel`** en npm (versión **`1.0.0`**).  
Sigue el patrón de diseño **Headless** (similar a Radix UI y Shadcn UI): no inyecta estilos CSS rígidos, sino que exporta componentes modulares de React listos para estilizar con **TailwindCSS**:

```tsx
import {
  EditorRoot,
  EditorContent,
  EditorCommand,
  EditorCommandList,
  EditorCommandItem,
  EditorCommandEmpty,
  EditorBubble,
  EditorBubbleItem,
  useEditor
} from "novel";
```

#### Componentes Principales:
1. **`EditorRoot` & `EditorContent`:** El contenedor principal y proveedor de estado de TipTap. Recibe extensiones, contenido inicial en JSON/Markdown y controladores de eventos (`onUpdate`).
2. **Slash Commands (`EditorCommand` con `cmdk`):** Se activa al escribir `/`. Trae comandos para títulos H1, H2, H3, listas de tareas con checkbox, bloques de código con syntax highlighting (Lowlight), citas y fórmulas matemáticas con KaTeX.
3. **Menú Flotante (`EditorBubble`):** Aparece automáticamente sobre cualquier texto seleccionado. Incluye botones de negrita, cursiva, selector de color y el botón de IA.
4. **Módulo de Inteligencia Artificial (`GenerativeMenuSwitch` + `AISelector`):**
   - Utiliza `@ai-sdk/react` (`useCompletion` de Vercel AI SDK) apuntando a un endpoint (ej. `/api/generate`).
   - Acciones preconfiguradas:
     - **Improve writing:** Mejora la redacción académica.
     - **Fix grammar:** Corrige ortografía y gramática.
     - **Make shorter / longer:** Resume o expande el texto.
     - **Continue writing:** Continúa la redacción a partir del párrafo previo.
     - **Caja de Prompt libre:** Permite escribir cualquier orden (ej. *"Alinea este párrafo a las normas APA 7"*).
   - Opciones al recibir el texto generado: **Replace selection**, **Insert below** o **Discard**.

---

## 🎯 3. Viabilidad de Uso para TesisMCP

| Criterio | Calificación | Veredicto Técnico |
| :--- | :---: | :--- |
| **Experiencia de Usuario (UX)** | ⭐⭐⭐⭐⭐ (5/5) | Es exactamente la experiencia tipo Notion / Google Docs moderna que buscábamos para el estudiante. |
| **Compatibilidad con TailwindCSS** | ⭐⭐⭐⭐⭐ (5/5) | Nativa. Todos los componentes se estilizan con clases estándar de Tailwind. |
| **Conexión con Backend Propio** | ⭐⭐⭐⭐⭐ (5/5) | El componente de IA solo hace un `POST` a `/api/generate`. En lugar de llamar a OpenAI directamente, podemos redirigirlo a nuestro backend de Django Ninja con los validadores Pydantic y el servidor MCP. |
| **Costo de Licencia** | ⭐⭐⭐⭐⭐ (5/5) | **$0.00**. Licencia Apache-2.0 completamente gratuita y de código abierto. |

### Recomendación de Adopción para el Rol 4 (Frontend):
Podemos adoptar Novel de dos formas:
1. **Instalando el paquete:** `npm i novel` en la aplicación de frontend de React/Next.js.
2. **Copiando los componentes (Estilo Shadcn UI):** Copiar directamente los archivos de `apps/web/components/tailwind/` del repositorio de GitHub. Esto le da al **Rol 4** control total del código, permitiendo cambiar colores, traducir los menús al español y personalizar los comandos para los pasos de tesis (`/problema`, `/hipotesis`, `/cita_apa`).

---

## 🔗 4. Referencias y Enlaces Oficiales

- [Sitio Web Oficial de Novel](https://novel.sh)
- [Documentación Oficial de Componentes](https://novel.sh/docs/introduction)
- [Repositorio en GitHub: steven-tey/novel](https://github.com/steven-tey/novel)
- [Paquete oficial en npm: novel](https://www.npmjs.com/package/novel)
