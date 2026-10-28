---
name: repository-hygiene-auditor
description: Audita la higiene del repositorio, previene la generación masiva accidental de archivos (explosiones de Markdown/artefactos), detecta fugas en .gitignore, archivos sobredimensionados, artefactos temporales y modificaciones fuera de alcance.
---

# Auditor de Higiene del Repositorio y Prevención de Fugas

Esta skill garantiza la **limpieza, orden y contención de archivos** en el proyecto TesisMCP. Evita la polución del árbol de directorios por herramientas automatizadas, artefactos de prueba o volcados incontrolados de documentación (como la creación accidental de miles de archivos Markdown derivados de exportaciones de grafos u Obsidian).

---

## 🧹 Los 7 Pilares de la Higiene de Repositorio

El agente debe aplicar estas comprobaciones antes de considerar finalizada cualquier intervención que cree o modifique archivos:

### 1. Control de Variación de Archivos (Baseline vs. Actual)
* **Verificación de Conteo:** Monitorear la cantidad total de archivos antes y después de ejecutar herramientas o scripts de generación (`find . -type f | wc -l`).
* **Detección de Anomalías:** Si un comando incrementa el número de archivos en más de 10-20 archivos inesperados, detener el flujo de inmediato, auditar los archivos generados y no reportar finalización hasta depurarlos.

### 2. Prevención de Explosiones de Documentación y Artefactos Accidentales
* **El Problema de los Markdown Masivos:** Herramientas de exportación, conversión o análisis (como vault export de Graphify, scrapers o generadores de grafos) pueden generar inadvertidamente cientos o miles de archivos `.md` en carpetas del proyecto.
* **Política de Contención:** Toda herramienta que genere archivos derivados debe confinarse a subdirectorios ignorados (`.cache/`, `tmp/`, `graphify-out/cache/`) o ejecutarse en modo memoria/AST sin volcado a disco.

### 3. Integridad de `.gitignore` y Prevención de Fugas
* **Verificación de Cobertura:** Comprobar que existan y se respeten las reglas para:
  - Entornos virtuales: `.venv/`, `env/`, `venv/`.
  - Caches de Python y pruebas: `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`.
  - Dependencias frontend: `node_modules/`.
  - Variables de entorno sensibles: `.env`, `.env.local`, `.env.*` (excepto `.env.example`).
  - Archivos temporales de Graphify: `graphify-out/cache/`, `graphify-out/converted/`, `graphify-out/obsidian/`.
  - Archivos del sistema operativo: `.DS_Store`, `Thumbs.db`.
* **Cero Caches Rastreados:** Ningún archivo de caché o compilado debe ser añadido al control de versiones.

### 4. Umbrales de Tamaño de Archivo (Large File Guard)
* **Alerta Temprana:** Detectar cualquier archivo generado o modificado que supere **500 KB** en código/documentación o **5 MB** en binarios.
* **Justificación Obligatoria:** Los únicos archivos de gran tamaño autorizados son los PDFs físicos comprobados en `docs/antecedentes_descargados/`. Ningún archivo de texto plano o JSON debe crecer desproporcionadamente sin justificación.

### 5. Barrido de Residuos y Artefactos Temporales
* Limpiar scripts temporales (`scratch_*.py`), volcados de depuración (`debug.log`, `temp_*.json`), archivos de backup de editores (`*.swp`, `*.bak`, `*~`) antes de reportar la tarea como cerrada.

### 6. Control de Alcance (Scope Guard)
* **Principio de Mínima Modificación:** No modificar archivos fuera del alcance directo de la petición del usuario.
* Si durante la tarea se detecta una mejora deseable en un componente no solicitado, documentarla como recomendación o consultarla, pero no aplicar modificaciones furtivas.

### 7. Control de Duplicados y Documentación Redundante
* Prohibido crear copias o clones derivados de archivos de documentación existentes con nombres como `informe_v2.md`, `copia_resumen.md` o carpetas espejo.
* Toda evolución documental debe realizarse sobre la fuente canónica en `docs/`.

---

## Protocolo de Limpieza Pre-Entrega

Antes de cerrar la tarea, ejecutar:
```bash
# 1. Comprobar que no haya residuos temporales ni caches fuera de lugar
find . -maxdepth 3 -type d -name "__pycache__" -o -name ".pytest_cache"
# 2. Comprobar archivos sobredimensionados inesperados
find . -not -path "*/.venv/*" -not -path "*/docs/antecedentes_descargados/*" -type f -size +2M
```
Si se detecta cualquier residuo o archivo accidental, limpiarlo antes de entregar.
