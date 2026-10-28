# BARRERA AUTOMÁTICA DE FINALIZACIÓN Y DEFINICIÓN DE TERMINADO (DOD GATE)

trigger: always_on

## Mandato Inviolable de Cierre de Tareas

El agente tiene **ESTRICTAMENTE PROHIBIDO** responder al usuario con afirmaciones de finalización como *"tarea completada"*, *"listo"*, *"los cambios funcionan correctamente"*, *"verificado"* o cerrar un hito de trabajo basándose únicamente en:
- Inspección visual de archivos.
- Razonamiento abstracto o memoria de contexto.
- Conjeturas de que el código no tiene errores.

---

## Protocolo Obligatorio Pre-Entrega

Antes de entregar cualquier cambio, el agente debe ejecutar obligatoriamente la suite determinista en terminal:

```bash
python3 scripts/verify_project.py
```

O, en su defecto, la cadena de comandos equivalentes comprobados:
1. `python3 -m core.grounding.audit_cli` (100% PDFs físicos verificados).
2. `DJANGO_DEBUG=1 .venv/bin/python backend/manage.py check` (0 errores de Django).
3. `DJANGO_DEBUG=1 .venv/bin/python backend/manage.py makemigrations --check --dry-run` (0 migraciones pendientes).
4. `DJANGO_DEBUG=1 .venv/bin/pytest --reuse-db -q` (100% pruebas unitarias e integración en verde).
5. Auditoría de Higiene (`repository-hygiene-auditor`): cero archivos masivos accidentales (prevención del problema de 1,730 Markdowns), cero fugas de `.gitignore`, cero cachés o archivos sobredimensionados no justificados.
6. Consistencia Código vs Documentación: conteo exacto de modelos (24), migraciones (18), pasos P01-P32 (32), herramientas MCP (34), prompts (35) y verificación de enlaces sin links rotos.

## Condición de Salida: Exit Code 0

- Si el código de salida de la verificación es **distinto de 0**, el agente **NO PUEDE** dar por terminada la respuesta. Debe auto-diagnosticar el fallo, corregir el código y volver a ejecutar la verificación.
- Toda entrega al usuario debe presentar la tabla de comandos ejecutados, tiempos, códigos de salida reales y el veredicto explícito `[APROBADO_CON_EVIDENCIA / EXIT_CODE_0]`.
