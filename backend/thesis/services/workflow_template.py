"""Plantilla base y utilidades de grafo para recorridos configurables."""

import hashlib
import json
from collections import defaultdict, deque
from typing import Any

from django.db import transaction

from thesis.models import (
    Project,
    ProjectWorkflow,
    WorkflowDependency,
    WorkflowPrompt,
    WorkflowTask,
)
from thesis.step_catalogue import CATALOGO_PASOS


DEFAULT_PROTECTED_STEPS: set[str] = {"P04", "P16", "P20", "P28"}

BASE_DEPENDENCIES: list[dict[str, Any]] = [
    {"source": "P02", "target": "P01", "field": "temas_propuestos", "reason": "Requiere temas candidatos para comparar"},
    {"source": "P03", "target": "P02", "field": "tema_ganador_titulo", "reason": "Requiere tema ganador"},
    {"source": "P04", "target": "P03", "field": "ods_principal_nombre", "reason": "Requiere tema alineado a ODS"},
    {"source": "P05", "target": "P04", "field": "titulo_oficial", "reason": "Requiere delimitación y título oficial"},
    {"source": "P06", "target": "P04", "field": "variables_confirmadas", "reason": "Problema debe mencionar variables confirmadas"},
    {"source": "P07", "target": "P06", "field": "pregunta_general", "reason": "Justificación parte del problema central"},
    {"source": "P08", "target": "P06", "field": "pregunta_general", "reason": "Aporte frente al problema planteado"},
    {"source": "P09", "target": "P04", "field": "variables_confirmadas", "reason": "Objetivo general debe mencionar variables confirmadas"},
    {"source": "P09", "target": "P06", "field": "preguntas_especificas", "reason": "Objetivos deben corresponder a preguntas"},
    {"source": "P10", "target": "P09", "field": "objetivos_especificos", "reason": "Preguntas específicas alineadas a objetivos"},
    {"source": "P11", "target": "P04", "field": "variables_confirmadas", "reason": "Hipótesis deben incluir variables de P04"},
    {"source": "P11", "target": "P09", "field": "objetivos_especificos", "reason": "Hipótesis específicas alineadas a objetivos"},
    {"source": "P12", "target": "P11", "field": "variable_independiente", "reason": "Operacionalización requiere variables de P11"},
    {"source": "P14", "target": "P04", "field": "titulo_oficial", "reason": "Inclusión y exclusión según delimitación del tema"},
    {"source": "P15", "target": "P14", "field": "criterios_inclusion", "reason": "Cribado PRISMA aplica criterios de inclusión"},
    {"source": "P16", "target": "P14", "field": "anio_inicio", "reason": "Filtro de años de P14"},
    {"source": "P17", "target": "P16", "field": "estudios", "reason": "Síntesis sobre matriz de literatura"},
    {"source": "P18", "target": "P17", "field": "patrones_metodologicos", "reason": "Brecha identificada a partir de patrones"},
    {"source": "P19", "target": "P16", "field": "estudios", "reason": "Redacción de antecedentes sobre matriz P16"},
    {"source": "P20", "target": "P16", "field": "estudios", "reason": "Referencias sobre estudios de P16"},
    {"source": "P21", "target": "P12", "field": "matriz_operacionalizacion", "reason": "Teorías base según constructos"},
    {"source": "P22", "target": "P11", "field": "variable_independiente", "reason": "Los constructos deben corresponder a variables registradas en P11"},
    {"source": "P22", "target": "P12", "field": "matriz_operacionalizacion", "reason": "Definiciones según variables"},
    {"source": "P23", "target": "P12", "field": "matriz_operacionalizacion", "reason": "Modelo conceptual según variables"},
    {"source": "P24", "target": "P11", "field": "hipotesis_general", "reason": "Proposiciones sustentan hipótesis"},
    {"source": "P24", "target": "P23", "field": "modelo_conceptual", "reason": "Proposiciones derivadas del modelo conceptual"},
    {"source": "P25", "target": "P11", "field": "tipo_investigacion", "reason": "Diseño metodológico según tipo y alcance"},
    {"source": "P26", "target": "P12", "field": "matriz_operacionalizacion", "reason": "Técnicas según dimensiones e indicadores"},
    {"source": "P27", "target": "P26", "field": "tecnicas", "reason": "Validez sobre instrumentos previstos"},
    {"source": "P28", "target": "P04", "field": "unidad_analisis_confirmada", "reason": "Ética sobre población y participantes"},
    {"source": "P29", "target": "P25", "field": "enfoque", "reason": "Redacción metodológica integra diseño"},
    {"source": "P29", "target": "P28", "field": "consentimiento_informado", "reason": "Redacción metodológica integra ética"},
    {"source": "P30", "target": "P12", "field": "matriz_operacionalizacion", "reason": "Ítems de cuestionario por dimensión de P12"},
    {"source": "P31", "target": "P12", "field": "matriz_operacionalizacion", "reason": "Guía de entrevista sobre variables de P12"},
    {"source": "P32", "target": "P30", "field": "banco_items", "reason": "Piloto calibra instrumento de P30"},
]


def detect_workflow_cycles(task_ids: list[str], dependencies: list[dict[str, Any]]) -> list[str]:
    """Detecta ciclos en el grafo dirigido de dependencias de tareas.
    
    Cada dependencia tiene:
      source: tarea dependiente (necesita al target)
      target: tarea prerrequisito (debe ejecutarse antes)
    Dirección del flujo de ejecución: target -> source
    """
    adj = defaultdict(list)
    for dep in dependencies:
        source = dep["source"]
        target = dep["target"]
        if source in task_ids and target in task_ids:
            # target precede a source
            adj[target].append(source)

    state = {t: 0 for t in task_ids}  # 0: UNVISITED, 1: VISITING, 2: VISITED
    path = []
    cycle = []

    def dfs(u: str) -> bool:
        state[u] = 1
        path.append(u)
        for v in adj[u]:
            if state[v] == 1:
                # Cycle found!
                idx = path.index(v)
                cycle.extend(path[idx:] + [v])
                return True
            elif state[v] == 0:
                if dfs(v):
                    return True
        path.pop()
        state[u] = 2
        return False

    for t in task_ids:
        if state[t] == 0:
            if dfs(t):
                return cycle
    return []


def calculate_workflow_hash(tasks_data: list[dict], deps_data: list[dict], prompts_data: dict[str, Any]) -> str:
    """Calcula un hash SHA-256 determinista del contenido del recorrido."""
    payload = {
        "tasks": sorted(tasks_data, key=lambda x: (x.get("order_index", 0), x.get("task_id", ""))),
        "dependencies": sorted(deps_data, key=lambda x: (x.get("source", ""), x.get("target", ""))),
        "prompts": {k: prompts_data[k] for k in sorted(prompts_data.keys())},
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def workflow_content_dump(workflow: ProjectWorkflow) -> tuple[list[dict], list[dict], dict[str, dict]]:
    """Serializa todos los campos mutables del recorrido para integridad y restauración."""
    tasks = list(workflow.tasks.select_related("prompt").order_by("task_id"))
    task_dump = [{
        "task_id": t.task_id, "legacy_step_code": t.legacy_step_code, "title": t.title,
        "description": t.description, "chapter_no": t.chapter_no, "order_index": t.order_index,
        "is_active": t.is_active, "is_optional": t.is_optional, "is_protected": t.is_protected,
        "contract_name": t.contract_name, "branch_condition": t.branch_condition,
        "output_schema": t.output_schema,
    } for t in tasks]
    prompts_dump = {
        t.task_id: {
            "text": t.prompt.prompt_text, "version": t.prompt.prompt_version,
            "provenance": t.prompt.provenance, "parameters_schema": t.prompt.parameters_schema,
        }
        for t in tasks if hasattr(t, "prompt") and t.prompt
    }
    deps_dump = [{
        "source": d.source_task.task_id, "target": d.target_task.task_id,
        "type": d.dependency_type, "required_field": d.required_field,
        "blocking": d.is_blocking, "reason": d.reason,
    } for d in workflow.dependencies.select_related("source_task", "target_task").order_by(
        "source_task__task_id", "target_task__task_id"
    )]
    return task_dump, deps_dump, prompts_dump


def initialize_project_workflow(
    project: Project,
    user: Any,
    base_template_version: str = "catalogo_p01_p32_v1",
    status: str = ProjectWorkflow.Status.PUBLISHED,
) -> ProjectWorkflow:
    """Crea e inicializa la plantilla base de recorrido para un proyecto."""
    from mcp_server.prompts.templates import TEMPLATES_POR_PASO

    with transaction.atomic():
        # Get next version number
        latest = ProjectWorkflow.objects.filter(project=project).order_by("-version_no").first()
        version_no = (latest.version_no + 1) if latest else 1

        wf = ProjectWorkflow.objects.create(
            project=project,
            version_no=version_no,
            status=status,
            base_template_version=base_template_version,
            change_summary="Inicialización de recorrido base P01-P32",
            created_by=user,
        )

        task_records = {}
        tasks_dump = []
        prompts_dump = {}

        for order, (code, info) in enumerate(CATALOGO_PASOS.items(), start=1):
            is_prot = code in DEFAULT_PROTECTED_STEPS
            is_opt = code == "P15"  # PRISMA es opcional por defecto en plantilla base
            t = WorkflowTask.objects.create(
                workflow=wf,
                task_id=code,
                legacy_step_code=code,
                title=info["nombre"],
                description=info["objetivo"],
                chapter_no=info["capitulo"],
                order_index=order,
                is_active=True,
                is_optional=is_opt,
                is_protected=is_prot,
                contract_name=f"{code}Output",
            )
            task_records[code] = t
            tasks_dump.append({
                "task_id": code,
                "order_index": order,
                "is_active": True,
                "is_optional": is_opt,
                "is_protected": is_prot,
            })

            # Prompt template
            template_info = TEMPLATES_POR_PASO.get(code, {})
            prompt_text = template_info.get("instrucciones_base", f"Instrucciones metodológicas para {info['nombre']}.")
            WorkflowPrompt.objects.create(
                task=t,
                prompt_text=prompt_text,
                prompt_version=1,
                provenance=WorkflowPrompt.Provenance.BASE_CATALOG,
                parameters_schema={"entradas_requeridas": info.get("entradas_requeridas", [])},
                created_by=user,
            )
            prompts_dump[code] = {
                "text": prompt_text, "version": 1,
                "provenance": WorkflowPrompt.Provenance.BASE_CATALOG,
                "parameters_schema": {"entradas_requeridas": info.get("entradas_requeridas", [])},
            }

        deps_dump = []
        for dep_info in BASE_DEPENDENCIES:
            s_code = dep_info["source"]
            t_code = dep_info["target"]
            if s_code in task_records and t_code in task_records:
                WorkflowDependency.objects.create(
                    workflow=wf,
                    source_task=task_records[s_code],
                    target_task=task_records[t_code],
                    dependency_type=WorkflowDependency.Type.DATA_REQUIRED,
                    required_field=dep_info.get("field", ""),
                    is_blocking=True,
                    reason=dep_info.get("reason", ""),
                )
                deps_dump.append({
                    "source": s_code, "target": t_code,
                    "type": WorkflowDependency.Type.DATA_REQUIRED,
                    "required_field": dep_info.get("field", ""),
                    "blocking": True, "reason": dep_info.get("reason", ""),
                })

        tasks_dump, deps_dump, prompts_dump = workflow_content_dump(wf)
        wf.content_sha256 = calculate_workflow_hash(tasks_dump, deps_dump, prompts_dump)
        wf.save(update_fields=["content_sha256", "updated_at"])

        return wf
