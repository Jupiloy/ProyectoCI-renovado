#!/usr/bin/env python3
"""
scripts/verify_project.py - Barrera Automática Determinista de Finalización (DoD Gate) para TesisMCP.

Este script ejecuta de manera rigurosa, no negociable e integral todas las comprobaciones
del sistema antes de permitir declarar una tarea como completada:

1. Auditoría Grounded (Anti-Alucinaciones): 9/9 PDFs físicos verificados al 100%.
2. Integridad del Sistema Django: manage.py check sin errores.
3. Integridad de Migraciones: manage.py makemigrations --check --dry-run sin discrepancias.
   Control separado: manage.py migrate --check sobre la base configurada, sin aplicar cambios.
4. Suite de Pruebas Automatizadas: pytest --reuse-db -q (100% verde).
5. Higiene de Repositorio (repository-hygiene-auditor): sin archivos masivos accidentales,
   sin fugas de .gitignore, sin caches residuales ni archivos sobredimensionados no autorizados.
6. Consistencia Código vs. Documentación:
   - Modelos Django exactos (59 tras BYOA local)
   - Migraciones activas (47, hasta 0047)
   - Pasos metodológicos P01-P32 (32)
   - Herramientas MCP (34) y Prompts MCP (35)
   - Enlaces internos en Markdown 100% válidos (0 rotos)
7. Auditoría Adversaria de Contratos (adversarial-code-auditor):
   - Validación estricta de esquemas Pydantic (StrictOutput, extra="forbid")
   - Búsqueda cruzada de mocks residuales en código de producción.

Retorna:
    0: Si todas las verificaciones pasan exitosamente [APROBADO_CON_EVIDENCIA].
    1: Si alguna verificación falla [RECHAZADO_CON_HALLAZGOS].
"""

import os
import sys
import time
import subprocess
import re
import urllib.parse
from pathlib import Path

# Configuración del entorno y auto-reexec en entorno virtual si existe
ROOT_DIR = Path(__file__).resolve().parent.parent
os.chdir(ROOT_DIR)

VENV_PYTHON = ROOT_DIR / ".venv" / "bin" / "python"
if VENV_PYTHON.exists() and sys.executable != str(VENV_PYTHON):
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

# Configurar sys.path y variables de entorno
sys.path.insert(0, str(ROOT_DIR / "backend"))
sys.path.insert(0, str(ROOT_DIR))

os.environ["DJANGO_DEBUG"] = "1"
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

ENV = os.environ.copy()
pythonpath = ENV.get("PYTHONPATH", "")
ENV["PYTHONPATH"] = f"{ROOT_DIR / 'backend'}:{ROOT_DIR}:{pythonpath}" if pythonpath else f"{ROOT_DIR / 'backend'}:{ROOT_DIR}"

VENV_PYTEST = ROOT_DIR / ".venv" / "bin" / "pytest"
PYTEST_EXEC = str(VENV_PYTEST) if VENV_PYTEST.exists() else "pytest"
PYTHON_EXEC = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

# Formato de salida ANSI
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


class VerificationSuite:
    def __init__(self):
        self.results = []
        self.start_time = time.time()

    def record(self, category: str, test_name: str, passed: bool, details: str, duration: float):
        self.results.append({
            "category": category,
            "name": test_name,
            "passed": passed,
            "details": details,
            "duration": duration,
        })
        icon = f"{GREEN}✅ PASÓ{RESET}" if passed else f"{RED}❌ FALLÓ{RESET}"
        print(f"[{icon}] {CYAN}{category}{RESET} -> {BOLD}{test_name}{RESET} ({duration:.2f}s)")
        if passed:
            print(f"       ↳ {details}")
        else:
            color = RED if not passed else YELLOW
            print(f"       {color}↳ Detalle: {details}{RESET}")

    def run_cmd(self, cmd: list[str], timeout: int = 120) -> tuple[int, str, str, float]:
        t0 = time.time()
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=ENV,
                cwd=ROOT_DIR,
                timeout=timeout
            )
            elapsed = time.time() - t0
            return res.returncode, res.stdout, res.stderr, elapsed
        except Exception as e:
            elapsed = time.time() - t0
            return 1, "", str(e), elapsed

    # 1. Auditoría Grounded
    def check_grounding_audit(self):
        cmd = [PYTHON_EXEC, "-m", "core.grounding.audit_cli"]
        code, out, err, elapsed = self.run_cmd(cmd)
        passed = code == 0 and "9/9 DOCUMENTOS VERIFICADOS AL 100% CON ÉXITO" in out
        details = "9/9 PDFs físicos validados (títulos y cifras literales)" if passed else (err or out).strip()[:200]
        self.record("Grounded Truth", "Auditoría de Documentos Base (PDFs)", passed, details, elapsed)

    # 2. Django System Check
    def check_django_health(self):
        cmd = [PYTHON_EXEC, "backend/manage.py", "check"]
        code, out, err, elapsed = self.run_cmd(cmd)
        passed = code == 0 and "no issues" in (out + err).lower()
        details = "0 errores o advertencias en configuración Django" if passed else (err or out).strip()[:200]
        self.record("Integridad Django", "manage.py check", passed, details, elapsed)

    # 3. Django Migraciones Check
    def check_django_migrations(self):
        cmd = [PYTHON_EXEC, "backend/manage.py", "makemigrations", "--check", "--dry-run"]
        code, out, err, elapsed = self.run_cmd(cmd)
        passed = code == 0 and "no changes detected" in (out + err).lower()
        details = "0 discrepancias entre modelos y archivos de migración" if passed else (err or out).strip()[:200]
        self.record("Integridad Django", "makemigrations --check --dry-run", passed, details, elapsed)

    def check_applied_migrations(self):
        # Se ejecuta antes de pytest: este consulta su propia base y no actualiza
        # la base de uso local. Este control nunca ejecuta migrate --noinput.
        cmd = [PYTHON_EXEC, "backend/manage.py", "migrate", "--check", "--database", "default"]
        code, out, err, elapsed = self.run_cmd(cmd)
        passed = code == 0
        details = "Sin migraciones pendientes en DATABASE_URL (alias default); no se aplicaron cambios"
        if not passed:
            details = "Base no actualizada o inaccesible; revisar conexión y ejecutar migrate --plan. "
            details += (err or out).strip()[:200] or "migrate --check rechazó el estado actual."
        self.record("Base de datos configurada", "migrate --check --database default", passed, details, elapsed)

    # 4. Pytest Suite
    def check_pytest_suite(self):
        cmd = [PYTEST_EXEC, "--reuse-db", "-q"]
        # La suite ya rozaba 300 s antes de B6.3/B6.4; deja margen a la ejecución PostgreSQL.
        code, out, err, elapsed = self.run_cmd(cmd, timeout=600)
        passed = code == 0 and ("passed" in out.lower() and "failed" not in out.lower())
        m = re.search(r"(\d+)\s+passed", out)
        count_str = f" ({m.group(1)} pruebas en verde)" if m else ""
        details = f"Suite de pruebas superada al 100%{count_str}" if passed else (err or out).strip()[:200]
        self.record("Pruebas Unitarias/Integración", "Pytest Suite Completa", passed, details, elapsed)

    # 5. Higiene del Repositorio (repository-hygiene-auditor)
    def check_repository_hygiene(self):
        t0 = time.time()
        errors = []

        # A. Verificar .gitignore
        gitignore = ROOT_DIR / ".gitignore"
        if not gitignore.exists():
            errors.append("No existe archivo .gitignore en la raíz")
        else:
            gi_text = gitignore.read_text(encoding="utf-8")
            required_patterns = [".venv", "__pycache__", ".pytest_cache", "var/", "node_modules"]
            for pat in required_patterns:
                if pat not in gi_text:
                    errors.append(f"Falta patrón obligatorio en .gitignore: '{pat}'")

        # B. Detección de archivos sobredimensionados (> 5MB fuera de PDFs y var/)
        large_files = []
        for path in ROOT_DIR.rglob("*"):
            if not path.is_file():
                continue
            path_str = str(path)
            # Ignorar entornos, control de versiones, dependencias instaladas por gestores
            # de paquetes (node_modules), carpeta var/ de modelos y PDFs descargados
            if (
                "/.venv/" in path_str
                or "/.git/" in path_str
                or "/node_modules/" in path_str
                or "/var/" in path_str
                or "/docs/antecedentes_descargados/" in path_str
                or "/graphify-out/" in path_str
            ):
                continue
            try:
                size_mb = path.stat().st_size / (1024 * 1024)
                if size_mb > 5.0:
                    large_files.append(f"{path.relative_to(ROOT_DIR)} ({size_mb:.2f} MB)")
            except Exception:
                pass
        if large_files:
            errors.append(f"Archivos sobredimensionados no autorizados (>5MB): {', '.join(large_files[:3])}")

        # C. Detección de explosiones de Markdown masivas (previene el caso de 1,730 markdowns)
        md_per_dir = {}
        for md_file in ROOT_DIR.glob("**/*.md"):
            if "/.venv/" in str(md_file) or "/.git/" in str(md_file) or "/node_modules/" in str(md_file) or "/graphify-out/" in str(md_file):
                continue
            parent = md_file.parent.relative_to(ROOT_DIR)
            md_per_dir[parent] = md_per_dir.get(parent, 0) + 1
        
        for p, count in md_per_dir.items():
            if count > 80:
                errors.append(f"Posible explosión de Markdowns: {p} contiene {count} archivos .md")

        # D. Detección de temporales y backups
        temp_files = []
        for pat in ["*.tmp", "*.swp", "*.bak", "*.orig", "*~"]:
            for tf in ROOT_DIR.glob(f"**/{pat}"):
                if "/.venv/" not in str(tf) and "/.git/" not in str(tf):
                    temp_files.append(str(tf.relative_to(ROOT_DIR)))
        if temp_files:
            errors.append(f"Residuos temporales encontrados: {', '.join(temp_files[:3])}")

        elapsed = time.time() - t0
        passed = len(errors) == 0
        details = "Árbol limpio: sin archivos masivos, sin residuos y con .gitignore íntegro" if passed else "; ".join(errors)
        self.record("Higiene de Repositorio", "Auditoría de Archivos y Fugas", passed, details, elapsed)

    # 6. Consistencia Documentación vs. Código (documentation-code-consistency)
    def check_doc_code_consistency(self):
        t0 = time.time()
        errors = []

        # A. Conteo de Modelos Django (59 esperados después de BYOA local)
        try:
            import django
            django.setup()
            from django.apps import apps
            thesis_models = list(apps.get_app_config("thesis").get_models())
            model_count = len(thesis_models)
            if model_count != 59:
                errors.append(f"Modelos Django discrepantes: encontrados {model_count}, esperados 59")
        except Exception as e:
            errors.append(f"Error importando modelos Django: {e}")

        # B. Conteo de Migraciones (47 esperadas: 0001 a 0047)
        mig_files = list((ROOT_DIR / "backend" / "thesis" / "migrations").glob("0*.py"))
        if len(mig_files) != 47:
            errors.append(f"Migraciones discrepantes: encontradas {len(mig_files)}, esperadas 47")

        # C. Conteo de Pasos Metodológicos (32 esperados: P01 a P32)
        try:
            import thesis.step_catalogue as sc
            steps_count = len(sc.CATALOGO_PASOS)
            if steps_count != 32:
                errors.append(f"Pasos metodológicos discrepantes: encontrados {steps_count}, esperados 32")
        except Exception as e:
            errors.append(f"Error importando CATALOGO_PASOS: {e}")

        # D. Conteo de Herramientas y Prompts MCP (34 herramientas, 35 prompts)
        try:
            import mcp_server.server as mcp_srv
            tools_count = len(mcp_srv.app._tool_manager._tools)
            prompts_count = len(mcp_srv.app._prompt_manager._prompts)
            if tools_count != 34:
                errors.append(f"Herramientas MCP discrepantes: registradas {tools_count}, esperadas 34")
            if prompts_count != 35:
                errors.append(f"Prompts MCP discrepantes: registrados {prompts_count}, esperados 35")
        except Exception as e:
            errors.append(f"Error comprobando servidor MCP: {e}")

        # E. Verificación de Enlaces Internos Markdown (Cero links rotos)
        broken_links = []
        docs_to_check = list((ROOT_DIR / "docs").glob("**/*.md")) + [ROOT_DIR / "README.md"]
        for doc in docs_to_check:
            text = doc.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
                link = m.group(2).strip()
                if link.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                path_part = link.split("#")[0].strip()
                if not path_part:
                    continue
                path_part = urllib.parse.unquote(path_part)
                if path_part.startswith("file://"):
                    target = Path(path_part[7:])
                else:
                    target = (doc.parent / path_part).resolve()
                if not target.exists():
                    broken_links.append(f"{doc.relative_to(ROOT_DIR)} -> {link}")

        if broken_links:
            errors.append(f"Enlaces Markdown rotos ({len(broken_links)}): {broken_links[:2]}")

        elapsed = time.time() - t0
        passed = len(errors) == 0
        details = (
            f"{model_count} modelos, {len(mig_files)} migraciones, {steps_count} pasos, "
            f"{tools_count} herramientas MCP, {prompts_count} prompts, "
            f"{len(docs_to_check)} Markdowns con 0 links rotos"
        ) if passed else "; ".join(errors)
        self.record("Consistencia Doc-Código", "Sincronización de Cifras y Enlaces", passed, details, elapsed)

    # 7. Auditoría Adversaria de Contratos (adversarial-code-auditor)
    def check_adversarial_contracts(self):
        t0 = time.time()
        errors = []

        try:
            from thesis.services.step_contracts import P01Output
            # 1. Validar que StrictOutput rechace campos espurios (extra="forbid")
            try:
                P01Output.model_validate({
                    "temas_propuestos": [
                        {
                            "id": i,
                            "titulo_tentativo": f"Tema tentativo de prueba {i}",
                            "pros": ["Pro verificado"],
                            "contras": ["Contra verificada"],
                            "viabilidad_preliminar": "ALTA"
                        } for i in range(1, 6)
                    ],
                    "tema_preseleccionado_id": 1,
                    "campo_espurio_prohibido": 123  # Debe fallar
                })
                errors.append("P01Output no rechazó un campo espurio (falla extra='forbid')")
            except Exception:
                pass  # Correcto: fue rechazado

            # 2. Validar que rechace lista con menos de 5 temas
            try:
                P01Output.model_validate({
                    "temas_propuestos": [
                        {
                            "id": 1,
                            "titulo_tentativo": "Tema tentativo de prueba 1",
                            "pros": ["Pro verificado"],
                            "contras": ["Contra verificada"],
                            "viabilidad_preliminar": "ALTA"
                        }
                    ],
                    "tema_preseleccionado_id": 1
                })
                errors.append("P01Output aceptó lista menor a 5 temas")
            except Exception:
                pass  # Correcto: rechazado
        except Exception as e:
            errors.append(f"Fallo importando/validando contratos Pydantic: {e}")

        # 3. Escaneo de tokens de prueba/mock en código de servicios de producción
        service_mocks = []
        for pyfile in (ROOT_DIR / "backend" / "thesis" / "services").glob("*.py"):
            content = pyfile.read_text(encoding="utf-8")
            if "2501.00001" in content or "mock_data_dummy" in content:
                service_mocks.append(str(pyfile.relative_to(ROOT_DIR)))
        if service_mocks:
            errors.append(f"Mocks residuales encontrados en servicios: {', '.join(service_mocks)}")

        elapsed = time.time() - t0
        passed = len(errors) == 0
        details = "Contratos Pydantic estrictos (extra='forbid') y 0 mocks en servicios de producción" if passed else "; ".join(errors)
        self.record("Auditoría Adversaria", "Validación de Contratos y Cero Mocks", passed, details, elapsed)

    def run_all(self) -> int:
        print("=" * 80)
        print(f"{BOLD}INICIANDO PUERTA AUTOMÁTICA DE VERIFICACIÓN (DEFINITION OF DONE GATE){RESET}")
        print(f"Directorio Raíz: {ROOT_DIR}")
        print(f"Intérprete Python: {PYTHON_EXEC}")
        print("=" * 80)

        self.check_grounding_audit()
        self.check_django_health()
        self.check_django_migrations()
        self.check_applied_migrations()
        self.check_pytest_suite()
        self.check_repository_hygiene()
        self.check_doc_code_consistency()
        self.check_adversarial_contracts()

        total_elapsed = time.time() - self.start_time
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["passed"])
        all_passed = (passed_tests == total_tests)

        print("\n" + "=" * 80)
        print(f"{BOLD}RESUMEN FINAL DE LA PUERTA DE VERIFICACIÓN (DoD){RESET}")
        print("=" * 80)
        print(f"Pruebas de Verificación: {passed_tests}/{total_tests} exitosas")
        print(f"Tiempo Total de Ejecución: {total_elapsed:.2f} segundos")
        
        if all_passed:
            print(f"\n{GREEN}{BOLD}VEREDICTO: [APROBADO_CON_EVIDENCIA / EXIT_CODE_0]{RESET}")
            print(f"{GREEN}Pasaron las comprobaciones ejecutadas. Esto no acredita validez científica, integraciones externas ni disponibilidad del despliegue.{RESET}\n")
            return 0
        else:
            print(f"\n{RED}{BOLD}VEREDICTO: [RECHAZADO_CON_HALLAZGOS / EXIT_CODE_1]{RESET}")
            print(f"{RED}Existen comprobaciones fallidas. Prohibido reportar la tarea como concluida hasta corregirlas.{RESET}\n")
            return 1


if __name__ == "__main__":
    suite = VerificationSuite()
    sys.exit(suite.run_all())
