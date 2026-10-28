# B10 — Operación local y despegue configurable

**Estado operativo local tras la reparación:** la base `tesismcp` de `tesismcp-local-pg` recibió las migraciones `0024`–`0044`, después de un respaldo conjunto DB+media y un ensayo de restauración/migración aislado. El desfase hasta `0023` fue el hallazgo inicial; las puertas históricas 7/7 no verificaban migraciones aplicadas. El verificador incorpora ahora ese control separado. Consultar el [registro B10](./paquete_b10_operacion_local_y_despliegue.md) para evidencia, comandos y límites; no confundir esta reparación local con el cierre de B10 o del producto.

**Estado:** recuperación local implementada y ensayada mediante respaldo conjunto DB+media, restauración aislada, migración y lectura funcional. La base activa ya recibió `0024`–`0044`. B10 sigue parcial: faltan política de ejecución automática/retención, copia independiente del disco y separación completa de parámetros de desarrollo/despliegue. No se afirma disponibilidad para usuarios externos. Las secciones 8 y 9 describen el procedimiento y su evidencia; la sección 2 conserva el hallazgo inicial.

## 1. Decisión de operación del equipo

Durante el desarrollo y el curso, TesisMCP corre localmente. El objetivo es conservar ese recorrido simple y reproducible y evitar decisiones que obliguen a usar un proveedor cloud antes de que el equipo lo elija. A la vez, configuración, almacenamiento y secretos deben poder cambiarse por entorno para preparar un despliegue posterior sin reescribir la lógica del dominio.

“Configurable para el despegue” significa que el entorno futuro puede especificar, sin cambiar reglas de negocio:

- conexión de PostgreSQL;
- modo debug, hosts, HTTPS, CSRF, cookies y proxy confiable;
- ubicación/backend de archivos privados;
- claves de aplicación e integraciones externas;
- número de workers y límites operativos;
- destino, horario y retención de backups;
- logs, health checks y monitoreo.

No significa que ya se pueda apuntar a cualquier hosting o storage cambiando una sola variable. Cada cambio de proveedor debe tener un adaptador/configuración compatible, una guía de operación y pruebas de despliegue/restauración.

## 2. Hallazgo inicial del 26/10/2026, antes de la reparación

### Ejecución y configuración

- `compose.yaml` define PostgreSQL 16 con pgvector y servicios opcionales mediante perfiles (`app`; GROBID usa su propio perfil). Los puertos publicados por esta configuración están ligados a `127.0.0.1`.
- La base usa el volumen persistente `tesismcp_postgres`; Compose declara volúmenes separados de media/modelos para la aplicación; no estaban creados ni montados en el inventario observado y solo PostgreSQL estaba activo. Se comprobó que el contenedor local `tesismcp-local-pg` monta `tesismcp_postgres` en `/var/lib/postgresql/data`.
- Django lee `DATABASE_URL`, pero en `compose.yaml` las credenciales de PostgreSQL y URLs de web/worker aún están fijadas al usuario `tesismcp` y contraseña de desarrollo `tesismcp_local`. `DJANGO_DEBUG` queda en modo de desarrollo por defecto. Esto no debe trasladarse a un entorno público.
- `MEDIA_ROOT` se deriva actualmente de una ruta de filesystem del proyecto. El almacenamiento Django configurado es `FileSystemStorage`; el Compose de aplicación declara un montaje para `/app/var/media`. No hay un backend de objeto remoto configurado.
- La configuración es **parcialmente portable** (por ejemplo, `DATABASE_URL` y varios ajustes se leen del entorno, pero el parser actual descarta parámetros de query como `sslmode`), pero Compose todavía necesita separar valores locales y futuros secretos/parámetros de despliegue. No existe `.env.example` en la raíz al corte de esta inspección.

### Backups PostgreSQL

Hay un helper heredado en `V1/scripts/respaldar_base.py`; no hay cron, timer o servicio Compose que lo ejecute automáticamente. El comando genera un dump PostgreSQL custom-format, valida que `pg_restore --list` pueda leer su catálogo y escribe una suma SHA-256. Su contenedor predeterminado es el antiguo `tesismcp-pg`, por lo que el contenedor actual se indicó explícitamente al crear la copia.

Durante la revisión se creó un dump de la base activa `tesismcp` en:

```text
V1/respaldos/tesismcp_respaldo_2026-10-26_222304.dump
```

El checksum de ese archivo se comprobó correctamente. También se comprobaron los checksums de cuatro dumps anteriores fechados el 21/10/2026. Esto prueba integridad respecto de sus sidecars y legibilidad del formato, pero **no equivale a una restauración probada** ni garantiza que las copias previas representen el estado actual.

Limitaciones de ese helper heredado y de ese primer dump (estado previo):

1. El comando es manual; no hay política de ejecución automática.
2. El dump protege solo PostgreSQL. No contiene PDFs, DOCX, datasets ni figuras bajo `MEDIA_ROOT`.
3. La copia recién creada reside en el mismo host y ruta de trabajo; no protege contra pérdida o daño de ese disco.
4. No se ha hecho restore drill a una instancia aislada.
5. No se ha fijado frecuencia ni retención. No purgar copias automáticamente hasta que el equipo defina esos valores.

Ese dump heredado fue una protección puntual; el respaldo conjunto y ensayo posterior se documentan en las secciones 8 y 9.

## 3. B10 por etapas

| Etapa | Resultado exigido | Alcance local/despliegue |
|---|---|---|
| B10.1 — Local reproducible | Arrancar DB, web y workers localmente mediante Compose; salud/errores visibles; puertos locales por defecto. | Mantener el camino de desarrollo en Podman y documentar comandos reales. |
| B10.2 — Configuración por entorno | Variables documentadas, `.env.example` sin secretos, defaults seguros para desarrollo y validación que impida arrancar un entorno de despliegue con claves/defaults inseguros. | `DATABASE_URL`, secretos, hosts, HTTPS/proxy, storage y concurrencia se configuran sin cambiar código de dominio. Separar override local y perfil de despliegue si es necesario. |
| B10.3 — Backup/restauración local | Script explícito y reproducible para PostgreSQL y archivos de usuario; hashes/manifiesto; restauración hacia destino aislado; evidencia de que los documentos enlazados vuelven a leerse. | Destino configurable y fuera de la carpeta versionada. No fijar frecuencia/retención sin decisión del equipo. El backup no se considera válido hasta probar restore. |
| B10.4 — Piloto no local | Entorno controlado con HTTPS, secretos externos, storage privado, monitoreo, worker, límites y responsables operativos; aceptación funcional y recuperación. | Solo después de elegir infraestructura y responsable. Ningún usuario externo antes de superar controles de seguridad y restauración. |

El trabajo de configuración puede empezar mientras se integra el frontend. La etapa B10.4 se cierra cuando exista un destino y un piloto a probar; no es necesario esperar a construir toda posible función del producto para preparar B10.1–B10.3.

## 4. Requisitos de backup y recuperación

La unidad de protección no es solo la fila SQL. Debe inventariarse qué archivos almacenados son necesarios para abrir cada objeto y preservar la correspondencia entre DB y archivos.

El diseño de backup debe cubrir, según su ubicación efectiva:

- PostgreSQL (dump consistente, checksum y versión de herramienta/servidor registrada);
- archivos originales y derivados referenciados desde PostgreSQL bajo `MEDIA_ROOT`;
- claves/configuración necesarias para operar, almacenadas por separado y con control de acceso; tratar el dump como sensible: puede incluir hashes de contraseña y credenciales cifradas de la aplicación; no publicar dumps ni sus manifiestos;
- metadatos/manifiesto suficientes para asociar copias de DB y media compatibles.

`var/models` parece contener modelos/cache de inferencia y no debe copiarse automáticamente sin inventariar si el equipo conserva allí artefactos propios irremplazables. No confundir cache regenerable con datos de tesis.

Todo restore drill debe realizarse contra una base y carpeta de medios aisladas; nunca sobrescribir la base activa como parte de una prueba. Verificar migraciones y hashes después de restaurar, recorrer al menos la lectura/descarga de archivos y registrar comandos, versiones, tiempos, errores y resultado. Si el restore falla, el backup no satisface el criterio.

Una copia en el mismo host sirve frente a ciertos errores lógicos, pero no frente a pérdida del equipo/disco. Antes del piloto, seleccionar destino separado (por ejemplo, disco externo cifrado o servicio institucional autorizado), responsable, frecuencia y retención. No fijar plazos sin acuerdo y requisitos institucionales.

## 5. Seguridad y configuración

- Los valores actuales `tesismcp_local` y `DEBUG=1` son solo defaults de desarrollo. El perfil local debe permanecer enlazado a loopback; el perfil de despliegue no debe heredar contraseña/secret key de desarrollo ni publicar PostgreSQL.
- No poner secretos en archivos versionados, frontend, logs, volcados de troubleshooting o prompts. `.env.example` contiene únicamente nombres y ejemplos no válidos como credenciales; el archivo `.env` real queda ignorado.
- En despliegue, fallar temprano si faltan `DJANGO_SECRET_KEY`, hosts/orígenes, credenciales DB u opciones obligatorias; no degradar silenciosamente a defaults locales.
- Configurar `DATABASE_URL`, rutas de media/storage y parámetros de worker por entorno. Si se elige object storage, adaptar el backend `STORAGES` y probar permisos, URLs privadas, hashes y borrado; no asumir que el Django `FileSystemStorage` actual ya funciona con almacenamiento remoto.
- Los backups son material sensible: permisos de filesystem restrictivos, destino protegido y cifrado en reposo conforme a la política que decida el equipo. El SHA-256 detecta cambios; **no cifra** el dump ni controla quién lo lee.
- Antes del piloto, definir cómo se renuevan/revocan secretos y cómo se recupera el servicio sin mostrar credenciales en logs.

## 6. Criterio de cierre

B10 no queda cerrado por tener un volumen, Dockerfile, Compose, un dump suelto o por pasar `manage.py check`. El cierre requiere:

1. Entorno local reproducible y sin publicación accidental en la red.
2. Configuración por entorno documentada, defaults de desarrollo separados y guardas de seguridad verificadas.
3. Backups de DB **y media** con checksums y destino configurado.
4. Restauración comprobada en entorno aislado y lectura funcional de los objetos restaurados.
5. Política/responsable de ejecución, destino, frecuencia, retención y eliminación aprobada por el equipo.
6. Para piloto no local: HTTPS, secretos, storage privado, monitoreo, límites, aceptación y recuperación probados en ese despliegue.
7. Documentación y contratos alineados, y puerta integral del proyecto con código 0.

## 7. Relación con los bloques restantes

B10 es transversal: la configuración y el backup local pueden avanzarse en paralelo con frontend; la revisión final de aceptación requiere un recorrido funcional integrado. B9 continúa condicionado por permisos de proveedor y no forma parte de la estrategia de backup. La integración del editor/frontend B1+B2 y la aceptación con usuarios siguen siendo trabajos separados.

## 8. Procedimiento reproducible de recuperación local

Herramienta canónica: [scripts/local_recovery.py](../../scripts/local_recovery.py). Reemplaza al helper de `V1` para los nuevos respaldos conjuntos; no borra los dumps históricos. Ejecutar desde la raíz de ProyectoCI. Requiere Python con biblioteca estándar y Podman; `--runtime docker` selecciona Docker. El subcomando `check-app` requiere además las dependencias Django del proyecto.

### Preparar una copia

1. Identificar la base y el `MEDIA_ROOT` usados realmente. En la inspección local, base `tesismcp`, contenedor `tesismcp-local-pg` y archivos en `var/media`. Un volumen Compose de media distinto necesita su ruta montada/accesible explícita; no copiar ciegamente el directorio por defecto.
2. Detener los escritores durante todo el respaldo: web, workers, MCP y cualquier otro proceso conectado. Si se usan los servicios del Compose raíz, los nombres son `web`, `worker` y `ai_worker`; comprobar también procesos fuera de Compose. El script no los detiene ni instala un modo mantenimiento distribuido.
3. Ejecutar:

```bash
python3 scripts/local_recovery.py backup \
  --container tesismcp-local-pg \
  --database tesismcp --user tesismcp \
  --media-root var/media \
  --destination var/backups \
  --maintenance-confirmed
```

El destino debe ser un directorio privado (0700). El comando crea un bundle único con `database.dump`, `media/`, `manifest.json` y `manifest.sha256`; archivos 0600. No utiliza temporales de dump dentro de PostgreSQL. Valida el catálogo del dump, hashes de archivos, referencias DB→media, huellas de filas de las tablas públicas, secuencias y esquema antes/después; rechaza cambios durante la copia y elimina su staging incompleto. La comprobación de sesiones y huellas ayuda a detectar actividad, pero no sustituye detener los escritores. La copia de media contiene todos los archivos regulares existentes, incluidos los no referenciados; rechaza enlaces y archivos especiales.

El manifiesto registra imagen PostgreSQL, versión de servidor/pg_dump y extensiones. Guarda hashes de filas, no contenido de filas. El dump sí contiene los datos privados. Los hashes detectan cambios respecto al manifiesto: no cifran ni prueban autenticidad frente a alguien que pueda reemplazar ambos. Se mantienen secretos de configuración y claves de cifrado fuera de este bundle; sin esas claves, credenciales cifradas restauradas pueden seguir siendo inutilizables.

### Verificar y restaurar sin tocar la instancia activa

Usar la ruta exacta `backup` devuelta por el comando anterior:

```bash
python3 scripts/local_recovery.py verify <ruta_del_bundle>
python3 scripts/local_recovery.py restore-isolated <ruta_del_bundle>
```

`verify` comprueba integridad de archivos/manifiesto y permisos; **no acredita recuperación SQL**. `restore-isolated` exige formato 2, crea un contenedor nuevo con la misma imagen PostgreSQL local, contraseña temporal aleatoria, red `none`, sin puertos publicados y PGDATA en tmpfs de 1 GiB. Requiere memoria suficiente: este ensayo está diseñado para la base local, no para bases grandes. No reemplaza ningún contenedor existente. Restaura mediante `pg_restore --exit-on-error --single-transaction`, copia media a un directorio nuevo bajo `var/recovery` y compara datos, secuencias, restricciones, índices, funciones, triggers y referencias de archivos. En caso de fallo elimina únicamente el entorno temporal recién creado.

Las restricciones `CHECK` se comparan normalizando un caso concreto de PostgreSQL: cast de un array de literales `varchar` a `text[]`, equivalente al cast individual de cada literal. No se omiten restricciones ni se ignoran cambios de valores permitidos; esto tiene una prueba de regresión. No se afirma que el comparador demuestre equivalencia semántica general de cualquier SQL.

La salida indica `container`, `media_root` y el informe privado. El contenedor se deja vivo para el ensayo de migraciones y lectura funcional; su tmpfs es temporal y no constituye otro backup. Al terminar, comprobar la etiqueta `org.tesismcp.recovery=1` del nombre devuelto y eliminar **solo ese contenedor** con `podman rm --force <nombre_del_ensayo>`. No usar comandos de limpieza global ni volúmenes de la base activa. Conservar el bundle y el informe; la copia de media del ensayo puede retirarse tras guardar evidencia.

### Ensayar migraciones y lectura

Ejecutar el código vigente con `DATABASE_URL` apuntando al contenedor aislado. Si se usa la imagen de verificación, compartir exclusivamente su red mediante `--network container:<nombre_del_ensayo>`, montar ProyectoCI en solo lectura, ocultar `.venv` del host y montar la media restaurada. Leer la contraseña temporal desde la configuración local de ese contenedor sin imprimirla; pasar la URL mediante entorno, no pegarla en documentación o logs.

Orden de comandos dentro del entorno con dependencias:

```bash
python backend/manage.py migrate --check
python backend/manage.py migrate --plan
python backend/manage.py migrate --noinput
python backend/manage.py migrate --check
python scripts/local_recovery.py check-app --media-root <media_restaurada_montada>
```

El primer check debe fallar si el backup quedó antes de las migraciones actuales. Ese fallo esperado confirma que se está comprobando la base restaurada. `check-app` usa una transacción de solo lectura: lista fuentes y extractos mediante servicios con el tesista real, abre archivos a través del storage Django y comprueba los hashes; para PDFs también ejecuta `pdfinfo`. No inicia sesiones con escritura ni llama a proveedores externos. No equivale a un recorrido completo del frontend ni prueba OAuth, correo o IA real.

En el host:

```bash
python3 scripts/local_recovery.py compare-legacy <ruta_del_bundle> \
  --container <nombre_del_ensayo> --media-root <media_restaurada>
```

Compara todas las columnas previas de cada tabla respaldada. Solo permite filas adicionales en `django_migrations`, `django_content_type` y `auth_permission`; ninguna fila previa puede desaparecer/cambiar. Si una migración futura transforma legítimamente columnas previas, este control fallará y se deberá inspeccionar y documentar la transformación; no relajar globalmente la comparación.

### Actualizar la base local y cerrar el ensayo

Solo después de un restore satisfactorio, ensayo de migraciones, preservación de datos y lectura funcional: comprobar que la base activa y media siguen en el estado respaldado, mantener escritores detenidos, aplicar las migraciones allí y repetir el check/lectura y comparación de datos previos. No restaurar el dump sobre la base activa para probarlo. Si la actualización falla, detenerse y diagnosticar; el backup probado permite preparar un entorno recuperado separado antes de decidir una sustitución controlada.

Finalmente ejecutar `TESISMCP_DB_CONTAINER=tesismcp-local-pg ./scripts/verify_podman.sh`, que ejecuta `python3 scripts/verify_project.py` con dependencias y PostgreSQL reales. La comprobación de migraciones aplicadas debe consultar la base indicada por `DATABASE_URL`, no la base temporal de pytest. Un `makemigrations --check` exitoso solo comprueba correspondencia entre modelos y archivos.

Este procedimiento sigue siendo manual. No instala timer/cron, no fija retención, no elimina copias previas y no copia automáticamente a otro disco. Las políticas y el destino independiente siguen pendientes de decisión.

## 9. Registro de la reparación ejecutada

Corte: noche del 26/10/2026 (America/Lima); los nombres de los bundles usan UTC del 27/10/2026. Instancia activa: `tesismcp-local-pg`, base/usuario `tesismcp`. PostgreSQL y `pg_dump`: `16.15 (Debian 16.15-1.pgdg12+2)`; extensión vector `0.8.7`. No se activó un servidor público ni un planificador.

Se respetó el orden: corregir el estado documental → respaldar DB+media → restaurar en aislamiento → ensayar y aplicar migraciones → añadir el control de migraciones aplicadas. La instancia inicialmente tenía `thesis` hasta `0023`; los archivos llegaban a `0044`. No se crearon migraciones nuevas: se aplicaron las 21 ya existentes tras inspeccionar su plan y sus operaciones.

**Bundle de recuperación probado:** `var/backups/backup-20261027T041734Z-e1225083`. Contiene la base **anterior** a la actualización (`0023`) y sus nueve archivos. Para recuperar ese corte usando el código vigente se restaura primero y se aplica después el mismo plan de migraciones ensayado; no anunciar que este dump contiene el esquema `0044`. Los backups previos se conservaron. Los dumps/manifiestos son privados y están bajo rutas ignoradas; no adjuntarlos a prompts ni publicarlos.

| Evidencia ejecutada | Tiempo | Salida / resultado |
|---|---:|---|
| Auditoría previa `python3 -m core.grounding.audit_cli` | 6.22 s | 0; 9/9 documentos |
| `local_recovery.py backup --container tesismcp-local-pg --maintenance-confirmed` (formato 2) | 154.57 s | 0; 45 tablas, nueve archivos y nueve referencias comprobadas |
| `local_recovery.py verify` sobre el bundle probado | 0.04 s | 0; integridad/permisos correctos |
| `local_recovery.py restore-isolated` | 74.60 s | 0; datos, secuencias, esquema y media coinciden con el alcance declarado |
| `manage.py migrate --check` antes de migrar la copia | 5.46 s | 1 esperado: detecta migraciones pendientes |
| `manage.py migrate --plan` en la copia | 5.70 s | 0; plan `0024`–`0044` inspeccionado |
| `manage.py migrate --noinput` en la copia | 14.57 s | 0; 21 migraciones aplicadas |
| `manage.py migrate --check` después en la copia | 12.32 s | 0; sin pendientes |
| `local_recovery.py compare-legacy` en la copia | 44.11 s | 0; preservadas filas/columnas previas de 45 tablas |
| `local_recovery.py check-app` en la copia | 9.11 s, incluido contenedor | 0; lectura de 15 proyectos, 25 fuentes y nueve archivos |
| Cotejo activo antes de migrar | 73.96 s | 0; DB/esquema/media iguales al backup y sin otras sesiones |
| `manage.py migrate --noinput` en la base activa | 27.25 s | 0; `0024`–`0044` aplicadas |
| `local_recovery.py compare-legacy` en la base activa | 49.88 s | 0; preservadas filas/columnas previas de 45 tablas y nueve referencias |
| `local_recovery.py check-app` en la base activa | 10.02 s, incluido contenedor | 0; lectura de 15 proyectos, 25 fuentes y nueve archivos |
| Nuevo control `check_applied_migrations()` en base activa | 5.48 s, incluido contenedor | 0; 44 migraciones `thesis` aplicadas y tablas de búsqueda presentes |
| Nuevo control `check_applied_migrations()` contra base vacía aislada | 8.17 s, incluido contenedor | 1 esperado: rechaza estado sin migraciones |
| Pruebas de guardas `pytest backend/thesis/tests/test_local_recovery.py -q -p no:cacheprovider` | 1.56 s de pytest | 0; once pruebas |

Las primeras dos restauraciones fueron rechazadas por la representación de tres casts `varchar[]`→`text[]` en restricciones `CHECK`, no por pérdida de filas. La segunda ejecución duró 80.25 s; se diagnosticaron las definiciones completas y se incorporó la normalización acotada descrita en el procedimiento. Ambos contenedores fallidos se eliminaron sin tocar la instancia activa. Un ensayo diagnóstico adicional se eliminó al finalizar. No se ocultó el fallo ni se desactivó la comprobación de restricciones.

Evidencia operacional detallada en archivos privados bajo `var/recovery`: `execution-evidence.json`, `django-commands.jsonl` y el `restore-report.json` del ensayo. El reporte de restauración acredita el momento anterior a migrar la copia; las comprobaciones posteriores tienen registros separados. El control de datos previos permite filas nuevas de permisos/tipos/migraciones que Django crea, pero no elimina ni cambia ninguna fila previa.

El contenedor de ensayo satisfactorio y su media temporal se retiraron después de las comprobaciones; se conservaron el bundle y los informes privados. No quedan contenedores de recuperación en ejecución.

**Verificación final ejecutada:** `TESISMCP_DB_CONTAINER=tesismcp-local-pg ./scripts/verify_podman.sh` ejecutó `python3 scripts/verify_project.py` en el contenedor de dependencias con PostgreSQL real: **8/8 controles, 214 pruebas aprobadas, exit code 0**, 508.47 s de gate (535.29 s incluido build/arranque; pytest 482.20 s). Salida completa en `var/recovery/verification-final.log` y resultado/tiempo en `var/recovery/verification-final.json`. **[APROBADO_CON_EVIDENCIA / EXIT_CODE_0]** para este alcance. Las cifras históricas de B8 no sustituyen esta ejecución. El gate no prueba periodicidad de backups, pérdida del disco, secretos externos ni disponibilidad del frontend.

**Pendiente después de esta reparación:** definir horario y retención de copias, destino fuera del mismo disco, custodia/recuperación de secretos, configuración segura por entorno (incluido el tratamiento de parámetros TLS en `DATABASE_URL`), despliegue y aceptación integrada. B9 y las integraciones externas siguen con sus condiciones anteriores. B10 completo sigue abierto.
