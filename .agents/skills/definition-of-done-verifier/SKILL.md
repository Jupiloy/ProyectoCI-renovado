---
name: definition-of-done-verifier
description: Barrera determinista y obligatoria de finalización (Definition of Done Gate). Impide declarar tareas concluidas basándose en inspección superficial o autoevaluación subjetiva. Exige ejecución real de scripts de verificación (python3 scripts/verify_project.py), pruebas automatizadas, integridad de esquemas, migraciones y enlaces.
---

# Verificador de Definición de Terminado (Definition of Done Verifier)

Esta skill es la **barrera final automatizada (DoD Gate)** de TesisMCP. Impide terminantemente que el agente asuma que el código funciona o declare un hito como "completado" sin haber ejecutado las comprobaciones automatizadas y haber obtenido un código de salida limpio (`exit code: 0`).

---

## 🚪 El Mandato Inviolable de la Barrera de Verificación

> **REGLA FUNDAMENTAL:**
> Queda terminantemente prohibido cerrar una tarea, emitir conclusiones o afirmar que un componente está "listo", "verificado" o "implementado" basándose únicamente en el razonamiento interno del agente, lecturas de código visuales o asunciones.
> Toda entrega **DEBE** ir precedida por la ejecución en terminal del script de verificación determinista:
> ```bash
> python3 scripts/verify_project.py
> ```
> O la ejecución manual verificada de la suite completa (`audit_cli`, `manage.py check`, `makemigrations --check`, `pytest`).

---

## 📋 Los 5 Criterios de la Definición de Terminado (DoD)

### 1. Ejecución de la Suite Determinista
Antes de entregar, es obligatorio ejecutar el script de verificación integral del proyecto:
```bash
python3 scripts/verify_project.py
```
* **Condición de Aprobación:** El código de salida **DEBE ser 0**.
* Si el código de salida es diferente de 0, el agente tiene la obligación de corregir la causa raíz de inmediato y volver a ejecutar la suite hasta obtener código 0 antes de comunicarse con el usuario.

### 2. Integridad de Migraciones y Modelos
* Ningún cambio en clases de modelos (`backend/thesis/models/*.py`) puede quedar sin su migración correspondiente.
* Ejecutar: `DJANGO_DEBUG=1 .venv/bin/python backend/manage.py makemigrations --check --dry-run` para garantizar sincronía total con la base de datos PostgreSQL.

### 3. Consistencia Cruzada entre Documentación y Código (Doc-Code Consistency)
Comprobar de forma programática que las afirmaciones en los archivos `.md` correspondan con el código real:
* **Número de modelos:** Conteo exacto de clases activas en código (34 modelos de dominio en el corte B1.1 de `backend/thesis/models/`) vs. tablas documentadas.
* **Número de migraciones:** Conteo de archivos de migración existentes (24 hasta `0024`) vs. historial documentado.
* **Pasos metodológicos:** Conteo exacto de pasos registrados (P01–P32 = 32 pasos en `thesis.step_catalogue.CATALOGO_PASOS`) vs. manuales.
* **Herramientas y Prompts MCP:** Conteo exacto de herramientas registradas en `mcp_server.server` (34 herramientas, 35 prompts) vs. lista en README.
* **Estilos de Citación:** Uniformidad estricta (APA 7 o IEEE) sin mezclar estilos dentro de un mismo documento.

### 4. Verificación de Enlaces en Documentación
* Todo enlace local en archivos Markdown (`[texto](ruta/archivo.md)` o `file://...`) debe apuntar a un archivo que exista físicamente en el disco.
* Prohibido dejar enlaces rotos o referencias a carpetas eliminadas/renombradas.

### 5. Análisis de Impacto de Cambios (Change Impact)
* Antes y después de modificar componentes compartidos, verificar los componentes dependientes utilizando herramientas de análisis estático o grafos de conocimiento (`graphify`):
  ```bash
  graphify query "qué componentes dependen de SourceDocument"
  # o graphify affected / path para verificar rutas de impacto
  ```
* Asegurar que las dependencias transitivas no sufran regresiones silenciosas.

---

## 📊 Formato Obligatorio de Reporte de Entrega

Toda respuesta final al usuario debe incluir la tabla de evidencia ejecutada:

| Verificación | Comando Ejecutado | Código de Salida | Estado |
| :--- | :--- | :---: | :---: |
| **Auditoría Grounded** | `python3 -m core.grounding.audit_cli` | `0` | ✅ PASÓ (9/9 PDFs) |
| **Integridad Django** | `python backend/manage.py check` | `0` | ✅ PASÓ (0 issues) |
| **Migraciones BD** | `python backend/manage.py makemigrations --check` | `0` | ✅ PASÓ (No changes) |
| **Pruebas Automatizadas** | `pytest --reuse-db -q` | `0` | ✅ PASÓ (informar el conteo real del corte) |
| **Higiene de Repositorio** | `repository-hygiene-auditor` | `0` | ✅ LIMPIO |
| **Consistencia Doc-Código**| `python3 scripts/verify_project.py` | `0` | ✅ SINCRONIZADO |

**Veredicto Final:** `[APROBADO_CON_EVIDENCIA / EXIT_CODE_0]`
