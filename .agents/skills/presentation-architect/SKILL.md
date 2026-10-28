---
name: presentation-architect
description: Diseñador y arquitecto visual de presentaciones ejecutivas y académicas de alto impacto. Transforma diapositivas aburridas y genéricas generadas por IA en presentaciones con diseño profesional de nivel humano (Bento grids, split-screens con diagramas enmarcados, métricas heroicas, contraste WCAG y notas de orador calibradas por tiempo). Diseñado para integrarse con gslides y herramientas de presentación.
---

# Presentation Architect: Diseño de Diapositivas de Alto Impacto

`presentation-architect` es una skill especializada en erradicar diapositivas "básicas" y mecánicas producidas por IA. Proporciona principios de diseño visual contemporáneo (estilo Bento, Keynote corporativo y pitch decks de tecnología), patrones de maquetación probados para el canvas de 720×405 pt y flujos de verificación visual iterativa.

---

## 🚫 Errores que Hacen que una Presentación se Vea "Básica" (Anti-Patrones)

1. **Repetir el mismo layout en todas las láminas:** Crear 3 tarjetas idénticas una tras otra en cada slide grita "generado por máquina".
2. **Párrafos largos de texto:** El público lee la lámina en vez de escuchar al expositor. Las diapositivas deben contener ideas clave en 4–6 palabras por viñeta, con palabras clave en **negrita**.
3. **Imágenes y diagramas flotando sin marco:** Pegar un PNG o captura en el centro sin contexto, borde, fondo de contraste ni puntos clave al lado destruye la estética.
4. **Falta de jerarquía tipográfica:** Títulos pequeños (<28pt) o cuerpos de texto minúsculos (<12pt) que nadie puede leer en un proyector o pantalla compartida.
5. **Cajas sólidas sin profundidad:** Usar rectángulos planos sin contraste de opacidad (`alpha`), sin bordes redondeados (`ROUND_RECTANGLE`) ni acentos visuales sutiles.
6. **Líneas genéricas debajo del título:** El clásico separador de 200px bajo el título en todas las láminas se siente anticuado. Es mejor un encabezado limpio o badges de categoría.

---

## 🎨 Patrones de Diseño de Alto Impacto (Canvas 720 × 405 pt)

### 1. Portada Ejecutiva con Profundidad
* **Fondo:** Dark tone de alta saturación (`#0D2137`, `#0F172A`, `#1E293B`).
* **Título:** 44–52pt en tipografía con personalidad (`Montserrat Bold`, `Poppins`, `Oswald`).
* **Badge / Tagline:** Pastilla redondeada superior indicando el contexto institucional o de curso.
* **Metadatos ordenados:** Autor, institución, fecha y versión en bloque inferior estructurado, nunca texto plano suelto.

### 2. Bento Grid Asimétrico (3–4 módulos)
En vez de 3 columnas iguales:
* **Módulo A (Principal / Hero, 55% ancho):** Idea central con mayor peso visual y fondo sutil.
* **Módulo B (Secundario, 45% ancho superior):** Métrica o diferenciador con número grande (32–40pt).
* **Módulo C (Secundario, 45% ancho inferior):** Lista de beneficios o tags en formato píldora.

### 3. Split-Screen con Enmarcado de Diagramas (Para Arquitecturas y Flujos)
* **Columna Izquierda (Ancho 240–280pt):**
  * Título de sección + subtítulo explicativo.
  * 3 a 4 viñetas clave con números destacados (`①`, `②`, `③` o badges circulares).
  * Conclusión o takeaway para el orador.
* **Columna Derecha (Ancho 380–420pt):**
  * Contenedor base de contraste (tarjeta con borde redondeado y sombra/borde sutil).
  * Imagen o diagrama insertado dentro del contenedor con proporciones preservadas (`maintain aspect ratio`).

### 4. Tarjetas de Métricas Heroicas (Stat Callouts)
* **Número Hero:** 48–64pt en negrita con el color de acento principal.
* **Etiqueta:** 12–14pt en negrita, todo mayúsculas o capitalizado.
* **Descripción de respaldo:** 10–11pt en tono atenuado (muted) que responde al *"¿y qué significa este número?"*.

### 5. Comparativa / Problema vs. Solución
* **Lado A (El Problema actual):** Fondo ligeramente rojizo o neutro apagado, iconos de fricción (`✕`, `!`), descripción del dolor.
* **Lado B (La Solución propuesta):** Fondo de acento positivo (esmeralda, azul tech), iconos de éxito (`✓`), descripción del valor.

---

## 📐 Paletas de Color Recomendadas

| Nombre | Fondo Principal | Fondo Tarjetas | Texto Principal | Acento Primario | Acento Secundario |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Emerald Tech** | `#0D2137` (Dark Navy) | `#142D47` / `#FFFFFF` | `#FFFFFF` / `#1E293B` | `#10B981` (Esmeralda) | `#06B6D4` (Cian) |
| **Midnight Executive** | `#0F172A` (Slate 900) | `#1E293B` (Slate 800) | `#F8FAFC` (Slate 50) | `#38BDF8` (Sky) | `#818CF8` (Indigo) |
| **Clean Crisp** | `#F8FAFC` (Off-white) | `#FFFFFF` | `#0F172A` (Slate 900) | `#2563EB` (Royal Blue) | `#059669` (Green) |
| **Charcoal Accent** | `#18181B` (Zinc 900) | `#27272A` (Zinc 800) | `#FAFAFA` (Zinc 50) | `#F59E0B` (Amber) | `#10B981` (Emerald) |

---

## ⏱️ Calibración para Exposiciones de 5 a 6 Minutos

Una exposición de 5 a 6 minutos (300 a 360 segundos) necesita un ritmo de **40 a 50 segundos por diapositiva** (máximo 7 a 8 diapositivas efectivas):

1. **Slide 1 (0:00 - 0:30):** Portada y presentación personal (30s).
2. **Slide 2 (0:30 - 1:15):** El Problema & Oportunidad (45s).
3. **Slide 3 (1:15 - 2:00):** La Propuesta de Valor / Concepto TesisMCP (45s).
4. **Slide 4 (2:00 - 3:00):** Flujo de Trabajo del Tesista y Asesor (con diagrama enmarcado) (60s).
5. **Slide 5 (3:00 - 4:00):** Arquitectura y Desacoplamiento MVC (con diagrama enmarcado) (60s).
6. **Slide 6 (4:00 - 4:45):** Stack Tecnológico e Innovación Determinista (45s).
7. **Slide 7 (4:45 - 5:30):** Estado Actual (Semana 10) y Entregables Validados (45s).
8. **Slide 8 (5:30 - 6:00):** Roadmap Futuro & Llamado a Preguntas (30s).

---

## 🛠️ Procedimiento de Implementación en Google Slides (`gslides`)

1. **Crear o resetear la presentación:** Generar el deck y eliminar los elementos por defecto (`i0`, `i1`).
2. **Generar el batch JSON con coordenadas rigurosas:**
   * Respetar los márgenes seguros (`x: 30` a `690`, `y: 20` a `385`).
   * Usar `ROUND_RECTANGLE` para tarjetas con contenido estructurado.
   * Utilizar `font_family: "Montserrat"` o `"Poppins"` para una sensación moderna.
3. **Insertar y enmarcar imágenes:**
   * Utilizar `insert-image-from-file`.
   * Redimensionar con `resize-element` conservando el aspect ratio original.
   * Colocar un contenedor o tarjeta de respaldo que le dé borde y acabado de mockup.
4. **Verificación visual obligatoria:**
   * Exportar miniaturas con `gslides readonly export-thumbnail PRESENTATION_ID output.png --slide SLIDE_ID`.
   * Inspeccionar con `read_file` cada diapositiva para validar que no haya texto cortado ni elementos superpuestos.
5. **Generar notas de orador (`set-notes`):**
   * Cada diapositiva DEBE contener un guión directo de exposición indicando el tiempo objetivo en segundos.
