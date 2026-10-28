---
name: docx-report-builder
description: Compilador y auditor inteligente de informes académicos y técnicos desde Markdown hacia Microsoft Word (.docx). Soporta maquetación IEEE (doble columna, Times New Roman, tablas estilizadas, citas numéricas [N] y referencias) y formatos institucionales. Incluye auditoría de integridad del archivo generado y sincronización con el Definition of Done Gate.
---

# Generador y Auditor de Informes en Word DOCX (docx-report-builder)

Esta skill permite compilar, formatear y auditar informes técnicos, papers y tesis desde archivos **Markdown** hacia documentos nativos de Microsoft Word (**`.docx`**), manteniendo estricta fidelidad tipográfica, tablas estructuradas, diagramas de arquitectura y normas bibliográficas (IEEE / APA).

---

## 🎯 Cuándo Usar Esta Skill
* Cuando el usuario solicite compilar, generar o actualizar el informe en Word (`.docx`) del proyecto o curso integrador.
* Cuando se hayan realizado cambios en el documento Markdown fuente (`informe_*.md`) y se requiera sincronizar la versión entregable en Word.
* Para auditar que el `.docx` resultante no esté corrupto, contenga todas las tablas e imágenes requeridas y pase la barrera determinista de verificación.

---

## ⚙️ Arquitectura del Pipeline

El flujo desacopla la redacción de la maquetación visual para evitar la corrupción de esquemas OOXML:

```
[Markdown Fuente (.md)] 
       │
       ▼
[Parser Semántico & Renderizador de Diagramas]
       │
       ▼
[Motor python-docx con Reglas Tipográficas IEEE]
       │
       ▼
[Documento Word Generado (.docx)]
       │
       ▼
[Auditoría de Integridad & Definition of Done Gate]
```

---

## 🚀 Flujo Operativo Paso a Paso

### Paso 1: Localización del Archivo Markdown Fuente
Identificar el documento Markdown a compilar. Por defecto en TesisMCP:
* **Informe IEEE del Curso Integrador:** `docs/06_informe_final_curso/informe_academico_curso_integrador_IEEE.md`.
* **Salida predeterminada:** `docs/06_informe_final_curso/informe_academico_curso_integrador_IEEE.docx`.

### Paso 2: Ejecución de la Compilación
Ejecutar el script compilador desde la raíz del proyecto usando el intérprete virtual:
```bash
# Compilación estándar (por defecto)
.venv/bin/python scripts/build_informe_ieee.py

# O especificando rutas personalizadas de entrada y salida
.venv/bin/python scripts/build_informe_ieee.py --input docs/ruta/informe.md --output docs/ruta/informe.docx
```

### Paso 3: Auditoría de Integridad del Archivo Generado
Verificar inmediatamente en la terminal que el archivo `.docx` se haya generado correctamente:
1. **Existencia y Tamaño:**
   ```bash
   ls -lh docs/06_informe_final_curso/*.docx
   ```
   *Comprobar que el tamaño esté entre 1 MB y 10 MB (con diagramas e imágenes incrustadas).*
2. **Ausencia de Corrupción:** Confirmar que no haya excepciones de empaquetado ZIP o esquemas XML rotos.
3. **Limpieza de Temporales:** El script utiliza `/tmp/tesis_mcp_ieee` para renderizar imágenes temporales; verificar que no queden residuos en el árbol de trabajo.

### Paso 4: Puerta de Verificación (Definition of Done Gate)
Ejecutar la suite determinista obligatoria para asegurar que la generación del `.docx` no haya dejado residuos ni roto enlaces en la documentación:
```bash
python3 scripts/verify_project.py
```
*El resultado debe retornar Código de Salida 0 (`exit code: 0`).*

---

## 📐 Especificaciones de Maquetación IEEE Implementadas

* **Tipografía:** Times New Roman.
  - Título Principal: 16 pt, negrita, centrado.
  - Encabezados Nivel 1 (H1): 11 pt, negrita, numeración romana en mayúsculas (`I. INTRODUCCIÓN`).
  - Encabezados Nivel 2 (H2): 10.5 pt, negrita, numeración arábiga (`1.1 Contexto`).
  - Texto Normal (Párrafos): 10 pt, interlineado 1.08, espaciado posterior 3 pt.
* **Columnas:** Doble columna (*two-column layout*) balanceada automáticamente en la última sección.
* **Márgenes:** Superior e inferior 1.7 cm; izquierdo y derecho 1.5 cm.
* **Paginación:** Campo de página dinámico centrado en el pie de página (`w:fldSimple w:instr="PAGE"`).
* **Tablas:** Cabecera con sombreado `#E9EDF1`, filas alternadas `#F8F9FA`, bordes sutiles y texto ajustado a 8-9 pt para evitar desbordes de columna.
* **Citas y Referencias:** Estilo numérico entre corchetes `[1]`, `[2]` con sección final de Referencias estructuradas.
