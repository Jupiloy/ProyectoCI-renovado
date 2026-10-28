"""Conector local polling entre TesisMCP y runtimes BYOA registrados."""

import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import requests
from django.core.management.base import BaseCommand, CommandError

from thesis.agent_runtimes import get_runtime_adapter


READ_ONLY_MCP_TOOLS = [
    "estado_servidor", "listar_pasos_mvp", "consultar_detalle_paso", "obtener_estado",
    "explorar_idea", "buscar_semantic_scholar", "buscar_antecedentes_peru", "listar_fuentes",
    "consultar_extractos", "listar_borradores", "consultar_borrador", "consultar_citas_borrador",
    "consultar_analisis_grobid", "consultar_trabajo", "buscar_pasajes", "consultar_capitulo",
    "consultar_observaciones", "localizar_frase", "listar_vinculos_evidencia",
]


def _workspace_mcp_overrides():
    """Desactiva copias TesisMCP globales para que el job use su token acotado."""
    global_config_path = Path.home() / ".gemini" / "config" / "mcp_config.json"
    if not global_config_path.exists():
        return {}
    try:
        config = json.loads(global_config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CommandError("No se pudo leer la configuración MCP global; no se inicia el agente para evitar usar credenciales amplias") from exc
    servers = config.get("mcpServers", {}) if isinstance(config, dict) else {}
    if not isinstance(servers, dict):
        raise CommandError("La configuración MCP global no tiene un mapa mcpServers válido")
    disabled = {}
    for name, entry in servers.items():
        if not isinstance(name, str) or not isinstance(entry, dict):
            continue
        identity = "".join(ch for ch in name.lower() if ch.isalnum())
        command_line = " ".join(str(value) for value in [entry.get("command", ""), *(entry.get("args", []) or [])]).lower()
        if "tesismcp" in identity or "mcp_server.server" in command_line:
            disabled[name] = {"disabled": True}
    return disabled


class Command(BaseCommand):
    help = "Conecta un runtime BYOA local con TesisMCP mediante jobs autenticados"

    def add_arguments(self, parser):
        parser.add_argument("--base-url", default=os.getenv("TESISMCP_API_BASE_URL", "http://127.0.0.1:8000"))
        parser.add_argument("--poll-interval", type=float, default=3.0)
        parser.add_argument("--runtime-path", default=os.getenv("TESISMCP_RUNTIME_EXECUTABLE", os.getenv("TESISMCP_AGY_PATH", "")))
        parser.add_argument("--model", default=os.getenv("TESISMCP_RUNTIME_MODEL", os.getenv("TESISMCP_AGY_MODEL", "")))
        parser.add_argument("--effort", choices=["low", "medium", "high"], default=os.getenv("TESISMCP_RUNTIME_EFFORT", os.getenv("TESISMCP_AGY_EFFORT", "medium")))
        parser.add_argument("--runtime", default=os.getenv("TESISMCP_RUNTIME", "ANTIGRAVITY_CLI"))
        parser.add_argument("--once", action="store_true", help="Consulta y procesa como máximo un job")

    def handle(self, *args, **options):
        base_url = options["base_url"].rstrip("/")
        if not base_url.startswith("https://") and not base_url.startswith("http://127.0.0.1") and not base_url.startswith("http://localhost"):
            raise CommandError("El conector requiere HTTPS fuera de localhost")
        if options["poll_interval"] < 1 or options["poll_interval"] > 60:
            raise CommandError("--poll-interval debe estar entre 1 y 60 segundos")
        connector_token = os.getenv("TESISMCP_CONNECTOR_TOKEN", "")
        mcp_token = os.getenv("TESISMCP_MCP_TOKEN", "")
        if not connector_token or not mcp_token:
            raise CommandError("Configura TESISMCP_CONNECTOR_TOKEN y TESISMCP_MCP_TOKEN en el entorno")
        try:
            adapter = get_runtime_adapter(options["runtime"])
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        executable = adapter.resolve_executable(options["runtime_path"])
        if not executable:
            raise CommandError(f"No se encontró el ejecutable del runtime {options['runtime']}; instálalo y autentícalo")
        api = f"{base_url}/api/v1/integrations/agents/connector"
        session = requests.Session()
        session.headers.update({"Authorization": f"Bearer {connector_token}"})
        self.stdout.write("Conector BYOA activo; esperando tareas asignadas")
        while True:
            try:
                response = session.post(f"{api}/claim", timeout=20)
                if response.status_code == 401:
                    raise CommandError("La credencial del conector venció o fue revocada")
                response.raise_for_status()
                job = response.json().get("job")
                if job:
                    self._run_job(job, api, session, executable, adapter, mcp_token, options)
                    if options["once"]:
                        return
                elif options["once"]:
                    return
                else:
                    time.sleep(options["poll_interval"])
            except requests.RequestException as exc:
                if options["once"]:
                    raise CommandError("No se pudo conectar con TesisMCP") from exc
                self.stderr.write("TesisMCP no está disponible; reintento en 5 segundos")
                time.sleep(5)

    def _run_job(self, envelope, api, session, executable, adapter, mcp_token, options):
        task = envelope["task"]
        job_id = envelope["job_id"]
        if envelope.get("runtime") != adapter.runtime_code:
            self._post_failure(session, api, job_id, "RUNTIME_UNAVAILABLE", "El job está asignado a otro runtime; configura el conector correspondiente")
            return
        prompt = (
            "Eres un agente metodológico que prepara una PROPUESTA para revisión humana en TesisMCP. "
            "No afirmes que la propuesta fue aprobada ni escribas contenido canónico. "
            "Usa solo el contexto recibido y las herramientas MCP de lectura permitidas; declara límites "
            "de evidencia y no inventes citas, páginas ni metadatos. Devuelve únicamente el objeto que "
            "cumpla el esquema JSON adjunto.\n\n"
            f"INSTRUCCIÓN METODOLÓGICA:\n{task.get('prompt_text') or 'Analiza la tarea y prepara la propuesta.'}\n\n"
            f"TAREA: {task['task_id']}\n"
            f"ENTRADAS:\n{json.dumps(task.get('input_data') or {}, ensure_ascii=False)}\n\n"
            f"CONTEXTO AUTORIZADO:\n{json.dumps(task.get('context_snapshot') or {}, ensure_ascii=False)}"
        )
        repository_root = Path(__file__).resolve().parents[4]
        with tempfile.TemporaryDirectory(prefix="tesismcp-byoa-") as temp_dir:
            workspace = Path(temp_dir)
            schema_path = workspace / "output-schema.json"
            schema_path.write_text(json.dumps(task["output_schema"], ensure_ascii=False), encoding="utf-8")
            schema_path.chmod(0o600)
            server_overrides = _workspace_mcp_overrides()
            server_overrides["tesismcp-byoa"] = {
                "command": sys.executable,
                "args": ["-m", "mcp_server.server"],
                "cwd": str(repository_root),
                "env": {
                    "DJANGO_SETTINGS_MODULE": "config.settings",
                    "DJANGO_DEBUG": "1",
                    "DATABASE_URL": os.getenv(
                        "DATABASE_URL",
                        "postgresql://tesismcp:tesismcp_local@127.0.0.1:5432/tesismcp",
                    ),
                    "TESISMCP_MCP_TOKEN": mcp_token,
                },
                "enabledTools": READ_ONLY_MCP_TOOLS,
                "timeoutSeconds": 600,
            }
            adapter.configure_mcp(workspace, server_overrides)
            args = adapter.build_command(
                executable, schema_path, model=options["model"], effort=options["effort"],
            )
            process = subprocess.Popen(
                args, cwd=workspace, text=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, bufsize=1, close_fds=True,
            )
            process.stdin.write(json.dumps({"event": "user", "message": {"content": prompt}}, ensure_ascii=False) + "\n")
            process.stdin.flush()
            process.stdin.close()
            stderr_lines = queue.Queue()
            stderr_thread = threading.Thread(
                target=self._drain_stderr, args=(process.stderr, stderr_lines), daemon=True,
            )
            stderr_thread.start()
            stop_heartbeat = threading.Event()
            cancelled = threading.Event()

            def heartbeat_loop():
                while not stop_heartbeat.wait(45):
                    try:
                        check = session.post(f"{api}/jobs/{job_id}/heartbeat", timeout=15)
                        if check.status_code == 401:
                            cancelled.set()
                            process.terminate()
                            return
                        check.raise_for_status()
                        if check.json().get("cancelled"):
                            cancelled.set()
                            process.terminate()
                            return
                    except requests.RequestException:
                        # El backend vence el lease si no vuelve la conexión.
                        continue

            heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
            heartbeat_thread.start()
            final_result = None
            try:
                for line in process.stdout:
                    event = adapter.parse_event(line)
                    if event is None:
                        continue
                    if event.kind == "tool_activity":
                        tool_name = (event.payload or {}).get("tool_name")
                        if tool_name in READ_ONLY_MCP_TOOLS:
                            self._post_event(session, api, job_id, "tool_activity", {"tool_name": tool_name})
                    elif event.kind == "progress":
                        self._post_event(session, api, job_id, "progress", event.payload or {})
                    elif event.kind == "result":
                        final_result = event.payload or {}
                return_code = process.wait(timeout=20)
            except Exception:
                process.kill()
                process.wait()
                raise
            finally:
                stop_heartbeat.set()
                heartbeat_thread.join(timeout=2)
                stderr_thread.join(timeout=2)
            stderr_summary = " ".join(list(stderr_lines.queue))
            if cancelled.is_set():
                return
            if adapter.permission_denied(stderr_summary):
                self._post_failure(session, api, job_id, "TOOL_PERMISSION_DENIED", "Antigravity bloqueó herramientas MCP; permite mcp(tesismcp-byoa/*) en sus permisos y vuelve a solicitar la tarea")
                return
            if return_code != 0 or not final_result or final_result.get("status") != "SUCCESS":
                error_code = "RUNTIME_FAILED"
                self._post_failure(session, api, job_id, error_code, "Antigravity no completó la tarea; revisa su estado y permisos")
                return
            structured = final_result.get("structured_output")
            if not isinstance(structured, dict):
                self._post_failure(session, api, job_id, "OUTPUT_INVALID", "Antigravity no devolvió la salida estructurada esperada")
                return
            self._request(session, "post", f"{api}/jobs/{job_id}/complete", json={
                "output_data": structured,
                "provenance": {
                    "model": options["model"] or None,
                    "conversation_id": final_result.get("conversation_id"),
                },
                "usage_data": final_result.get("usage") or {},
            })

    @staticmethod
    def _drain_stderr(stream, output_queue):
        for line in stream:
            if output_queue.qsize() < 40:
                output_queue.put(line.strip()[:500])

    def _post_event(self, session, api, job_id, event_type, payload):
        try:
            self._request(session, "post", f"{api}/jobs/{job_id}/events", json={"type": event_type, "payload": payload})
        except requests.RequestException:
            pass

    def _post_failure(self, session, api, job_id, error_code, message):
        try:
            self._request(session, "post", f"{api}/jobs/{job_id}/fail", json={"error_code": error_code, "message": message})
        except requests.RequestException:
            self.stderr.write(f"No se pudo informar el fallo del job {job_id}; el lease vencerá en el backend")

    @staticmethod
    def _request(session, method, url, **kwargs):
        response = session.request(method, url, timeout=30, **kwargs)
        response.raise_for_status()
        return response.json()
