# Contratos de backend para TesisMCP

El acceso, la selección y la creación de proyectos ya consumen la API Django desde
`src/App.tsx` y `src/api/`. Las cinco pantallas académicas de ejemplo permanecen
aisladas en `src/DemoApp.tsx`. Falta comprobar el recorrido con una cuenta real
y un navegador. Ver `../docs/02_arquitectura_y_sistema/paso_1_acceso_y_seleccion_proyecto.md`.

El transporte `src/api/client.ts` usa `/api/v1`, cookies y CSRF. Sus cabeceras
opcionales no sustituyen los campos `expected_version` e `idempotency_key` que
el backend exige en el JSON de determinadas operaciones futuras.

## Contratos y conexiones restantes

1. **Sesión y permisos**
   - Conectados en 1B: estado de sesión, login, logout, CSRF y permisos por proyecto.
   - Pendiente: comprobar expiración y navegación en navegador con cuenta real.

2. **Proyectos**
   - Conectados en 1B: listado autorizado paginado, creación, selección y estado del proyecto.
   - Pendientes: integrantes, invitaciones, datos institucionales y vistas académicas del proyecto.

3. **Documento y versiones**
   - Estructura del documento, bloques editables y formato.
   - Guardado, control de concurrencia y conflictos de versión.
   - Envíos al asesor, snapshots históricos y exportaciones congeladas.

4. **Recorrido metodológico**
   - Catálogo de pasos y recorrido configurado para cada proyecto.
   - Orden, dependencias, estados, prompts y versiones.
   - Permisos y validaciones para cambios que afecten dependencias.

5. **Fuentes y referencias**
   - Carga, procesamiento, estado de lectura y procedencia.
   - Disponibilidad de texto completo, resumen o metadatos.
   - Pasajes localizados y ubicación física verificable.
   - Datos de referencia IEEE editables.

6. **Consulta y agente**
   - Selección de fuentes, consultas y resultados trazables.
   - Estado opcional del agente, tareas, errores y cancelación.
   - Separación entre evidencia localizada y propuesta generada.

7. **Revisión**
   - Comentarios anclados, respuestas y estado de resolución.
   - Solicitud de cambios y decisiones del asesor.
   - Regla de aprobación cuando existen observaciones abiertas.

8. **Integraciones**
   - Autorización y sincronización opcional con Zotero.
   - Alcance real de búsquedas o importaciones asistidas desde catálogos.
   - Capacidades MCP habilitadas para cada proyecto.
