#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
CONTAINER_RUNTIME="${CONTAINER_RUNTIME:-podman}"
DB_CONTAINER="${TESISMCP_DB_CONTAINER:-tesismcp-local-pg}"
VERIFY_IMAGE="${TESISMCP_VERIFY_IMAGE:-localhost/tesismcp-verify:local}"
DATABASE_URL="${TESISMCP_VERIFY_DATABASE_URL:-postgresql://tesismcp:tesismcp_local@127.0.0.1:5432/tesismcp}"
AUDIT_REPORT="docs/04_modulo_investigacion_y_busqueda/auditoria_grounded_resultados.json"

if ! command -v "$CONTAINER_RUNTIME" >/dev/null 2>&1; then
    echo "No se encontró el runtime de contenedores: $CONTAINER_RUNTIME" >&2
    exit 2
fi

if ! "$CONTAINER_RUNTIME" inspect --format '{{.State.Running}}' "$DB_CONTAINER" 2>/dev/null | grep -qx true; then
    echo "El contenedor PostgreSQL '$DB_CONTAINER' no está en ejecución." >&2
    echo "Inícialo o define TESISMCP_DB_CONTAINER con el nombre del contenedor activo." >&2
    exit 2
fi

if ! "$CONTAINER_RUNTIME" exec "$DB_CONTAINER" pg_isready >/dev/null; then
    echo "PostgreSQL no está listo dentro de '$DB_CONTAINER'." >&2
    exit 2
fi

"$CONTAINER_RUNTIME" build --tag "$VERIFY_IMAGE" "$ROOT_DIR"

"$CONTAINER_RUNTIME" run --rm \
    --network host \
    --user 0:0 \
    --volume "$ROOT_DIR:$ROOT_DIR:ro" \
    --volume "$ROOT_DIR/$AUDIT_REPORT:$ROOT_DIR/$AUDIT_REPORT:rw" \
    --volume "$ROOT_DIR/.venv" \
    --workdir "$ROOT_DIR" \
    --env DJANGO_DEBUG=1 \
    --env "DATABASE_URL=$DATABASE_URL" \
    --env PYTHONDONTWRITEBYTECODE=1 \
    --env PYTEST_ADDOPTS="-p no:cacheprovider" \
    "$VERIFY_IMAGE" python scripts/verify_project.py
