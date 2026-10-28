#!/usr/bin/env python3
"""Respaldo local PostgreSQL + media y restauración exclusivamente aislada.

Requiere detener web/workers y otros escritores durante backup. No es un
planificador, un respaldo de roles/claves de cifrado ni una copia fuera del disco.
Solo usa stdlib y el cliente PostgreSQL del contenedor existente.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import uuid


ROOT = Path(__file__).resolve().parent.parent
REFERENCES = {
    "source_document": [("storage_key", "sha256"), ("derived_storage_key", "derived_sha256")],
    "manuscript_document": [("storage_key", "sha256")],
    "research_dataset_version": [("storage_key", "sha256")],
    "research_figure_version": [("storage_key", "output_sha256")],
}


def run(args, **kwargs):
    return subprocess.run(args, check=True, timeout=600, **kwargs)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def safe_path(path):
    path = Path(os.path.abspath(path))
    if any(part.is_symlink() for part in [path, *path.parents]):
        raise ValueError("No se admiten rutas con enlaces simbólicos")
    return path


def private_directory(path):
    path = safe_path(path)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    # No cambiar permisos de una carpeta compartida preexistente.
    if path.stat().st_mode & 0o077:
        raise ValueError(f"El directorio debe tener permisos 0700: {path}")
    return path


def media_inventory(root):
    root = safe_path(root)
    if not root.is_dir():
        raise ValueError("MEDIA_ROOT no existe; no se sustituye por una copia vacía")
    result = {}
    for path in sorted(root.rglob("*")):
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ValueError("Media contiene un enlace o archivo especial")
        result[str(path.relative_to(root))] = {"bytes": path.stat().st_size, "sha256": sha(path)}
    return result


def copy_media(source, destination, inventory):
    destination.mkdir(mode=0o700)
    for key in inventory:
        relative = Path(key)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Ruta media fuera del directorio")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with safe_path(source / relative).open("rb") as src, target.open("xb") as dst:
            shutil.copyfileobj(src, dst)
        target.chmod(0o600)
    if media_inventory(destination) != inventory:
        raise ValueError("La copia media no coincide con el inventario")


def identifier(value):
    return '"' + value.replace('"', '""') + '"'


def canonical_constraints(definitions):
    """pg_dump/restore redistribuye el cast varchar[] -> text[] en cada literal.

    Normalizar SOLO ese caso con literales (sin funciones, NULL ni expresiones).
    No eliminar casts ni comparar únicamente nombres: una restricción debilitada
    o un valor permitido diferente tiene que cambiar el fingerprint.
    """
    literal = r"'(?:[^']|'')*'::character varying"
    pattern = rf"\(ARRAY\[({literal}(?:,\s*{literal})*)\]\)::text\[\]"
    return re.sub(pattern, lambda match: "ARRAY[" + ", ".join(
        f"({value})::text" for value in re.findall(literal, match.group(1))
    ) + "]", definitions)


class Database:
    def __init__(self, runtime, container, database, user):
        self.runtime, self.container, self.database, self.user = runtime, container, database, user

    def command(self, command, *args, interactive=False):
        return [self.runtime, "exec", *(["-i"] if interactive else []), self.container,
                command, "-U", self.user, "-d", self.database, *args]

    def sql(self, query):
        cmd = [self.runtime, "exec", "-e", "PGOPTIONS=-c timezone=UTC -c default_transaction_read_only=on",
               self.container, "psql", "-X", "-q", "-A", "-t", "-v", "ON_ERROR_STOP=1",
               "-U", self.user, "-d", self.database, "-c", query]
        return run(cmd, capture_output=True, text=True).stdout.strip()

    def require_idle(self):
        count = self.sql("SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()")
        if count != "0":
            raise ValueError("Hay otras sesiones en la base: detener web, workers y demás escritores")

    def schema(self):
        rows = self.sql("""SELECT json_build_array(table_name, column_name) FROM information_schema.columns
            WHERE table_schema='public' AND table_name IN
            (SELECT tablename FROM pg_tables WHERE schemaname='public')
            ORDER BY table_name, ordinal_position""")
        result = {}
        for line in rows.splitlines():
            table, column = json.loads(line)
            result.setdefault(table, []).append(column)
        return result

    def inventory(self, columns=None):
        result = {}
        for table, fields in (columns if columns is not None else self.schema()).items():
            query = f"SELECT row_to_json(t)::text FROM (SELECT {','.join(map(identifier, fields))} FROM public.{identifier(table)}) t"
            # Solo se persisten hashes; nunca filas, correos, hashes de contraseñas o claves.
            hashes = sorted(hashlib.sha256(line.encode()).hexdigest() for line in self.sql(query).splitlines())
            result[table] = {"columns": fields, "rows": len(hashes), "row_hashes": hashes}
        return result

    def structure(self):
        result = {}
        queries = {
            "constraints": "SELECT conrelid::regclass::text, conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE connamespace='public'::regnamespace ORDER BY 1,2",
            "triggers": "SELECT tgrelid::regclass::text,tgname,pg_get_triggerdef(oid),tgenabled FROM pg_trigger WHERE NOT tgisinternal AND tgrelid IN (SELECT oid FROM pg_class WHERE relnamespace='public'::regnamespace) ORDER BY 1,2",
            "indexes": "SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY 1,2",
            "functions": "SELECT proname,pg_get_function_identity_arguments(oid),prosrc FROM pg_proc WHERE pronamespace='public'::regnamespace ORDER BY 1,2",
            "extensions": "SELECT extname,extversion FROM pg_extension ORDER BY 1",
        }
        for label, query in queries.items():
            definition = self.sql(query)
            if label == "constraints":
                definition = canonical_constraints(definition)
            result[label] = hashlib.sha256(definition.encode()).hexdigest()
        result["sequences"] = {}
        for seq in self.sql("SELECT sequencename FROM pg_sequences WHERE schemaname='public' ORDER BY 1").splitlines():
            result["sequences"][seq] = self.sql(f"SELECT last_value,is_called FROM public.{identifier(seq)}")
        return result

    def check_references(self, files):
        tables = self.schema()
        checked = 0
        for table, pairs in REFERENCES.items():
            if table not in tables:
                continue
            for key, digest in pairs:
                rows = self.sql(f"SELECT json_build_array({identifier(key)},{identifier(digest)}) FROM public.{identifier(table)} WHERE {identifier(key)} IS NOT NULL AND {identifier(key)}<>''")
                for row in rows.splitlines():
                    name, expected = json.loads(row)
                    if name not in files or files[name]["sha256"] != expected:
                        raise ValueError(f"Referencia sin archivo/hash coincidente en {table}.{key}")
                    checked += 1
        return checked


def write_json(path, content):
    with path.open("x", encoding="utf-8") as out:
        json.dump(content, out, ensure_ascii=False, indent=2)
        out.write("\n")
    path.chmod(0o600)


def verify_bundle(bundle):
    bundle = safe_path(bundle)
    for path in [bundle, *bundle.rglob("*")]:
        mode = path.lstat().st_mode
        if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)) or mode & 0o077:
            raise ValueError("Respaldo con permisos públicos, enlaces o archivos especiales")
    if sha(bundle / "manifest.json") != (bundle / "manifest.sha256").read_text().strip():
        raise ValueError("Hash del manifiesto incorrecto")
    data = json.loads((bundle / "manifest.json").read_text())
    if data["format_version"] not in {1, 2} or sha(bundle / "database.dump") != data["dump_sha256"]:
        raise ValueError("Formato/hash del dump incorrecto")
    if media_inventory(bundle / "media") != data["media"]:
        raise ValueError("Media incompleto o modificado")
    return data


def backup(args):
    if not args.maintenance_confirmed:
        raise ValueError("Detener escritores y pasar --maintenance-confirmed; el script no los detiene")
    media = safe_path(args.media_root)
    destination = private_directory(args.destination)
    if media == destination or media in destination.parents or destination in media.parents:
        raise ValueError("Media y destino de backup no deben contenerse entre sí")
    db = Database(args.runtime, args.container, args.database, args.user)
    db.require_idle()
    before = db.inventory()
    structure = db.structure()
    files = media_inventory(media)
    references = db.check_references(files)
    image = run([args.runtime, "inspect", args.container, "--format", "{{.Image}}"], capture_output=True, text=True).stdout.strip()
    name = "backup-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8]
    stage = Path(tempfile.mkdtemp(prefix=".incomplete-", dir=destination))
    try:
        with (stage / "database.dump").open("xb") as out:
            run(db.command("pg_dump", "-Fc"), stdout=out)
        with (stage / "database.dump").open("rb") as src:
            run([args.runtime, "exec", "-i", args.container, "pg_restore", "--list"], stdin=src, stdout=subprocess.DEVNULL)
        copy_media(media, stage / "media", files)
        db.require_idle()
        if before != db.inventory() or structure != db.structure() or files != media_inventory(media):
            raise ValueError("La base/media cambió durante el respaldo; no se publica como válido")
        write_json(stage / "manifest.json", {
            "format_version": 2, "created_at": datetime.now(timezone.utc).isoformat(),
            "database": args.database, "user": args.user, "source_container": args.container,
            "postgres_image_id": image, "dump_sha256": sha(stage / "database.dump"),
            "postgres_version": db.sql("SHOW server_version"),
            "extensions": db.sql("SELECT extname,extversion FROM pg_extension ORDER BY 1"),
            "pg_dump_version": run([args.runtime, "exec", args.container, "pg_dump", "--version"], capture_output=True, text=True).stdout.strip(),
            "media": files, "verified_file_references": references, "tables": before, "structure": structure,
        })
        (stage / "manifest.sha256").write_text(sha(stage / "manifest.json") + "\n")
        verify_bundle(stage)
        final = destination / name
        stage.rename(final)
        return {"backup": str(final), "tables": len(before), "files": len(files), "references": references}
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def restore_isolated(args):
    bundle = safe_path(args.bundle)
    data = verify_bundle(bundle)
    if data["format_version"] != 2:
        raise ValueError("Crear un nuevo backup formato 2 para comparar restricciones normalizadas")
    parent = private_directory(args.destination)
    name = "tesismcp-recovery-" + uuid.uuid4().hex[:12]
    directory = parent / name
    directory.mkdir(mode=0o700)
    created = False
    try:
        env = os.environ.copy()
        env["POSTGRES_PASSWORD"] = secrets.token_urlsafe(32)
        run([args.runtime, "create", "--name", name, "--network", "none",
             "--label", "org.tesismcp.recovery=1", "--tmpfs", "/var/lib/postgresql/data:rw,size=1g",
             "--env", f"POSTGRES_USER={data['user']}", "--env", f"POSTGRES_DB={data['database']}",
             "--env", "POSTGRES_PASSWORD", data["postgres_image_id"]], env=env, stdout=subprocess.DEVNULL)
        created = True
        run([args.runtime, "start", name], stdout=subprocess.DEVNULL)
        db = Database(args.runtime, name, data["database"], data["user"])
        for _ in range(60):
            ready = subprocess.run(db.command("pg_isready", "-h", "127.0.0.1"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            if ready.returncode == 0:
                break
            time.sleep(1)
        else:
            raise ValueError("PostgreSQL aislado no inició")
        with (bundle / "database.dump").open("rb") as src:
            run(db.command("pg_restore", "--exit-on-error", "--single-transaction", interactive=True), stdin=src)
        copy_media(bundle / "media", directory / "media", data["media"])
        restored_tables = db.inventory()
        restored_structure = db.structure()
        differences = [f"table:{key}" for key in set(restored_tables) | set(data["tables"])
                       if restored_tables.get(key) != data["tables"].get(key)]
        differences += [f"structure:{key}" for key in restored_structure
                        if restored_structure[key] != data["structure"].get(key)]
        if differences:
            raise ValueError("Restauración difiere en: " + ", ".join(sorted(differences)))
        references = db.check_references(media_inventory(directory / "media"))
        report = {"container": name, "backup": str(bundle), "media_root": str(directory / "media"),
                  "restore_verified": True, "verified_file_references": references,
                  "verification_scope": "public table rows, sequences, schema fingerprints (normalized CHECK casts), media hashes",
                  "network": "none", "host_ports": [], "temporary_pgdata": True}
        write_json(directory / "restore-report.json", report)
        return report
    except BaseException:
        if created:
            subprocess.run([args.runtime, "rm", "--force", name], stdout=subprocess.DEVNULL, timeout=60)
        shutil.rmtree(directory)
        raise


def compare_legacy(args):
    data = verify_bundle(safe_path(args.bundle))
    db = Database(args.runtime, args.container, data["database"], data["user"])
    current = db.inventory({table: info["columns"] for table, info in data["tables"].items()})
    additions = {"auth_permission", "django_content_type", "django_migrations"}
    changed = []
    for table, before in data["tables"].items():
        if table in additions:
            if Counter(before["row_hashes"]) - Counter(current[table]["row_hashes"]):
                changed.append(table)
        elif before != current[table]:
            changed.append(table)
    if changed:
        raise ValueError(f"Filas previas modificadas/eliminadas: {', '.join(changed)}")
    references = db.check_references(media_inventory(args.media_root))
    return {"legacy_tables_preserved": len(current), "verified_file_references": references}


def check_application(args):
    """Leer con el código Django vigente, sin login con escritura ni llamadas externas."""
    sys.path.insert(0, str(ROOT / "backend"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()
    from django.core.files.storage import default_storage
    from django.db import connection, transaction
    from django.test import override_settings
    from thesis.models import ProjectParticipant, SourceDocument
    from thesis.services.sources import list_excerpts, list_sources

    if connection.vendor != "postgresql":
        raise ValueError("La lectura de recuperación exige PostgreSQL real")
    files = media_inventory(args.media_root)
    read_files, listed, projects = 0, 0, 0
    with override_settings(MEDIA_ROOT=str(safe_path(args.media_root))), transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
        for member in ProjectParticipant.objects.filter(role="OWNER", active=True, project__status="ACTIVE").select_related("user", "project"):
            rows = list_sources(member.user, member.project_id)
            listed += len(rows)
            projects += 1
            for row in rows:
                list_excerpts(member.user, member.project_id, row["source_id"], limit=1)
        for source in SourceDocument.objects.exclude(storage_key__isnull=True).exclude(storage_key=""):
            if source.storage_key not in files:
                raise ValueError("Falta un archivo de fuente restaurada")
            with default_storage.open(source.storage_key, "rb") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != source.sha256:
                    raise ValueError("Django leyó bytes distintos del hash persistido")
            if source.storage_key.lower().endswith(".pdf"):
                # Lectura física del PDF, sin mostrar contenido ni modificarlo.
                run(["pdfinfo", str(args.media_root / source.storage_key)], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            read_files += 1
    return {"projects_read_via_services": projects, "sources_listed": listed,
            "source_files_read_via_django_storage": read_files, "database_read_only": True}


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", default="podman", choices=["podman", "docker"])
    sub = parser.add_subparsers(dest="action", required=True)
    b = sub.add_parser("backup")
    b.add_argument("--container", required=True)
    b.add_argument("--database", default="tesismcp")
    b.add_argument("--user", default="tesismcp")
    b.add_argument("--media-root", type=Path, default=ROOT / "var/media")
    b.add_argument("--destination", type=Path, default=ROOT / "var/backups")
    b.add_argument("--maintenance-confirmed", action="store_true")
    v = sub.add_parser("verify")
    v.add_argument("bundle", type=Path)
    r = sub.add_parser("restore-isolated")
    r.add_argument("bundle", type=Path)
    r.add_argument("--destination", type=Path, default=ROOT / "var/recovery")
    c = sub.add_parser("compare-legacy")
    c.add_argument("bundle", type=Path)
    c.add_argument("--container", required=True)
    c.add_argument("--media-root", type=Path, required=True)
    a = sub.add_parser("check-app")
    a.add_argument("--media-root", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    try:
        if args.action == "backup":
            result = backup(args)
        elif args.action == "restore-isolated":
            result = restore_isolated(args)
        elif args.action == "compare-legacy":
            result = compare_legacy(args)
        elif args.action == "check-app":
            result = check_application(args)
        else:
            data = verify_bundle(args.bundle)
            result = {"checksums_verified": True, "files": len(data["media"])}
        result["elapsed_seconds"] = round(time.monotonic() - started, 2)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        # No imprimir salida SQL o contenido privado del dump en errores.
        print(f"ERROR ({time.monotonic() - started:.2f}s): {type(error).__name__}: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
