"""Figuras PNG versionadas desde resultados tabulares congelados; nunca ejecuta código."""

import hashlib
import json
import math
import textwrap
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import UUID

from django.conf import settings
from django.db import IntegrityError, transaction

from thesis.models import ResearchFigure, ResearchFigureVersion, ResearchTableRecipeVersion
from thesis.services.access import require_project
from thesis.services.errors import DomainError

RENDERER_VERSION = "b8.3.1-pillow"
WIDTH, HEIGHT = 1200, 800
MAX_BAR_POINTS, MAX_CONTINUOUS_POINTS = 30, 500
_CHART_TYPES = {"BAR", "LINE", "SCATTER"}


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _number(value):
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not result.is_finite():
        return None
    converted = float(result)
    return converted if math.isfinite(converted) else None


def _font(size):
    from PIL import ImageFont
    candidate = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    if not candidate.is_file():
        raise DomainError("FIGURE_RENDERER_UNAVAILABLE", "Falta DejaVu Sans para el renderer determinista")
    return ImageFont.truetype(str(candidate), size=size)


def _font_fingerprint():
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    if not font_path.is_file():
        raise DomainError("FIGURE_RENDERER_UNAVAILABLE", "Falta DejaVu Sans para el renderer determinista")
    return _sha(font_path.read_bytes())


def _render_png(spec, values, columns):
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise DomainError("FIGURE_RENDERER_UNAVAILABLE", "Pillow no está disponible en el servidor") from exc
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    title_font, label_font, small_font = _font(30), _font(21), _font(16)
    left, right, top, bottom = 115, 1120, 130, 670
    for line_no, line in enumerate(textwrap.wrap(spec["title"], width=58)[:3]):
        draw.text((left, 20 + 34 * line_no), line, fill="#172554", font=title_font)
    draw.line((left, top, left, bottom), fill="#475569", width=3)
    draw.line((left, bottom, right, bottom), fill="#475569", width=3)
    draw.text((left, 710), spec["x_label"], fill="#1f2937", font=label_font)
    draw.text((left, 95), spec["y_label"], fill="#1f2937", font=label_font)
    ys = [point[1] for point in values]
    ymin, ymax = min(0.0, min(ys)), max(0.0, max(ys))
    if ymin == ymax:
        ymax = ymin + 1.0
    yspan = ymax - ymin
    def py(y):
        return int(bottom - ((y - ymin) / yspan) * (bottom - top))
    for tick in range(5):
        val = ymin + yspan * tick / 4
        y = py(val)
        draw.line((left, y, right, y), fill="#e2e8f0", width=1)
        draw.text((8, y - 10), f"{val:.3g}", fill="#475569", font=small_font)
    n = len(values)
    baseline = py(0.0)
    draw.line((left, baseline, right, baseline), fill="#64748b", width=2)
    x_numbers = [point[0] for point in values] if spec["chart_type"] in {"LINE", "SCATTER"} else []
    x_min, x_max = (min(x_numbers), max(x_numbers)) if x_numbers else (0, max(n - 1, 1))
    if x_min == x_max:
        x_max = x_min + 1
    if x_numbers:
        for tick in range(5):
            value = x_min + (x_max - x_min) * tick / 4
            px = int(left + tick * (right - left) / 4)
            draw.line((px, top, px, bottom), fill="#f1f5f9", width=1)
            draw.text((px - 24, bottom + 12), f"{value:.3g}", fill="#475569", font=small_font)
    coords = []
    for index, (xval, yval, label) in enumerate(values):
        if x_numbers:
            px = int(left + ((xval - x_min) / (x_max - x_min)) * (right - left))
        else:
            px = int(left + (index + 0.5) * (right - left) / max(n, 1))
        coords.append((px, py(yval)))
        if spec["chart_type"] == "BAR":
            bar_width = max(2, int((right-left) / max(n, 1) * 0.64))
            draw.rectangle((px-bar_width//2, min(py(yval), baseline), px+bar_width//2,
                            max(py(yval), baseline)), fill="#2563eb")
        elif spec["chart_type"] == "SCATTER":
            draw.ellipse((px-6, py(yval)-6, px+6, py(yval)+6), fill="#2563eb")
        if n <= 20 and not x_numbers:
            label_text = str(label)[:18]
            draw.text((px-35, bottom+12), label_text, fill="#475569", font=small_font)
    if spec["chart_type"] == "LINE" and len(coords) > 1:
        draw.line(coords, fill="#2563eb", width=4)
        for px, py_ in coords:
            draw.ellipse((px-5, py_-5, px+5, py_+5), fill="#1d4ed8")
    output = tempfile.SpooledTemporaryFile(max_size=4 * 1024 * 1024)
    image.save(output, format="PNG", optimize=False, compress_level=9)
    output.seek(0)
    return output.read()


def _check_result(version):
    encoded = _canonical(version.result_json)
    if _sha(encoded) != version.result_sha256:
        raise DomainError("OUTPUT_INVALID", "El hash del resultado tabular no coincide")
    result = version.result_json
    columns, rows = result.get("columns"), result.get("rows")
    if (not isinstance(columns, list) or not columns or not isinstance(rows, list) or not rows
            or any(not isinstance(row, dict) or set(row) != set(columns) for row in rows)):
        raise DomainError("OUTPUT_INVALID", "La tabla versionada tiene una estructura inválida")
    if result.get("input", {}).get("sha256") != version.expected_input_sha256:
        raise DomainError("OUTPUT_INVALID", "La procedencia de la tabla no coincide con su versión")
    return columns, rows


def _normalize_spec(spec, version, *, accept_truncated_input):
    columns, rows = _check_result(version)
    required = {"chart_type", "x_column", "y_column", "title", "x_label", "y_label", "alt_text"}
    if not isinstance(spec, dict) or set(spec) != required:
        raise DomainError("VALIDATION_ERROR", "La figura requiere chart_type, x_column, y_column, title, x_label, y_label y alt_text")
    kind = spec["chart_type"]
    if (not isinstance(kind, str) or kind not in _CHART_TYPES
            or not isinstance(spec["x_column"], str) or not isinstance(spec["y_column"], str)
            or spec["x_column"] not in columns or spec["y_column"] not in columns):
        raise DomainError("VALIDATION_ERROR", "Tipo de gráfico o columnas no válidos")
    for key, maximum in (("title", 180), ("x_label", 100), ("y_label", 100), ("alt_text", 500)):
        value = spec[key]
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
            raise DomainError("VALIDATION_ERROR", f"{key} es obligatorio y tiene un límite de {maximum} caracteres")
    if type(accept_truncated_input) is not bool:
        raise DomainError("VALIDATION_ERROR", "accept_truncated_input debe ser booleano")
    if version.result_json.get("truncated") and not accept_truncated_input:
        raise DomainError("TRUNCATED_INPUT_CONFIRMATION_REQUIRED", "La tabla está truncada; confirma explícitamente que la figura use esas filas")
    max_points = MAX_BAR_POINTS if kind == "BAR" else MAX_CONTINUOUS_POINTS
    if len(rows) > max_points:
        raise DomainError("FIGURE_TOO_MANY_POINTS", f"{kind} admite como máximo {max_points} filas; reduce la tabla mediante su receta")
    points = []
    for index, row in enumerate(rows):
        y_value = _number(row.get(spec["y_column"]))
        if y_value is None:
            raise DomainError("VALIDATION_ERROR", "La columna y debe contener solo números finitos y no vacíos")
        x_value = row.get(spec["x_column"])
        if x_value is None or (isinstance(x_value, str) and not x_value.strip()):
            raise DomainError("VALIDATION_ERROR", "La columna x no puede contener valores vacíos")
        if kind == "BAR":
            points.append((index, y_value, x_value))
        else:
            x_number = _number(x_value)
            if x_number is None:
                raise DomainError("VALIDATION_ERROR", "LINE y SCATTER requieren una columna x numérica en este renderer")
            points.append((x_number, y_value, x_value))
    if kind in {"LINE", "SCATTER"}:
        points.sort(key=lambda point: point[0])
    clean = {key: spec[key].strip() if isinstance(spec[key], str) else spec[key] for key in sorted(spec)}
    return clean, points, {"alt_text": clean["alt_text"], "description": clean["title"],
                           "x_label": clean["x_label"], "y_label": clean["y_label"],
                           "source_truncated": bool(version.result_json.get("truncated")),
                           "source_row_count": len(rows), "accessibility_reviewed": False}


def _version_data(version):
    return {"id": str(version.id), "figure_id": str(version.figure_id), "version_no": version.version_no,
            "source_result_sha256": version.source_result_sha256, "spec": version.spec_json,
            "spec_sha256": version.spec_sha256, "output_sha256": version.output_sha256,
            "size_bytes": version.size_bytes, "mime_type": version.mime_type,
            "width": version.width, "height": version.height, "renderer_version": version.renderer_version,
            "accessibility": version.accessibility_json, "created_by_id": version.created_by_id,
            "created_at": version.created_at.isoformat()}


def create_figure(actor, project_id, dataset_id, recipe_id, table_version_no, name, spec,
                  idempotency_key, expected_version=None, accept_truncated_input=False):
    project = require_project(actor, project_id, owner_only=True)
    try:
        key = UUID(str(idempotency_key))
    except (ValueError, TypeError, AttributeError) as exc:
        raise DomainError("VALIDATION_ERROR", "idempotency_key debe ser UUID") from exc
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 160:
        raise DomainError("VALIDATION_ERROR", "name debe contener entre 1 y 160 caracteres")
    source = ResearchTableRecipeVersion.objects.filter(
        recipe_id=recipe_id, recipe__dataset_version__dataset__project=project,
        recipe__dataset_version__dataset_id=dataset_id, version_no=table_version_no,
    ).select_related("recipe").first()
    if source is None:
        raise DomainError("NOT_FOUND", "Versión de tabla no encontrada")
    clean_spec, points, accessibility = _normalize_spec(
        spec, source, accept_truncated_input=accept_truncated_input,
    )
    spec_hash = _sha(_canonical(clean_spec))
    try:
        from PIL import __version__ as pillow_version
    except ImportError as exc:
        raise DomainError("FIGURE_RENDERER_UNAVAILABLE", "Pillow no está disponible en el servidor") from exc
    renderer_version = f"{RENDERER_VERSION}-{pillow_version}-dejavu-{_font_fingerprint()[:16]}"
    output = _render_png(clean_spec, points, source.result_json["columns"])
    output_hash = _sha(output)
    identity = ResearchFigure.objects.filter(table_version=source, name=name.strip()).first()
    if identity is None and expected_version is not None:
        raise DomainError("VERSION_CONFLICT", "expected_version no aplica al crear una figura")
    if identity is not None and expected_version is None:
        raise DomainError("VALIDATION_ERROR", "expected_version es obligatorio al versionar una figura existente")
    try:
        with transaction.atomic():
            figure = (ResearchFigure.objects.create(table_version=source, name=name.strip(), created_by=actor)
                      if identity is None else ResearchFigure.objects.select_for_update().get(pk=identity.pk))
            previous = figure.versions.filter(idempotency_key=key).first()
            if previous:
                if previous.spec_sha256 != spec_hash or previous.source_result_sha256 != source.result_sha256:
                    raise DomainError("VERSION_CONFLICT", "La clave idempotente ya se usó con otra figura")
                return {"figure": _figure_data(figure), "version": _version_data(previous),
                        "created": False, "idempotent": True}
            latest = figure.versions.order_by("-version_no").first()
            current_no = latest.version_no if latest else 0
            if current_no != (expected_version or 0):
                raise DomainError("VERSION_CONFLICT", "La figura cambió; vuelve a consultar su versión vigente")
            storage_root = Path(settings.MEDIA_ROOT).resolve()
            relative = Path("figures") / str(project.id) / str(figure.id) / f"v{current_no + 1}-{output_hash}.png"
            path = (storage_root / relative).resolve()
            if not path.is_relative_to(storage_root):
                raise DomainError("OUTPUT_INVALID", "La ruta de almacenamiento calculada no es segura")
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                if _sha(path.read_bytes()) != output_hash:
                    raise DomainError("OUTPUT_INVALID", "Ya existe una salida distinta en la ruta versionada")
            else:
                with path.open("xb") as stream:
                    stream.write(output)
            version = ResearchFigureVersion.objects.create(
                figure=figure, version_no=current_no + 1, idempotency_key=key,
                source_result_sha256=source.result_sha256, spec_json=clean_spec, spec_sha256=spec_hash,
                storage_key=relative.as_posix(), output_sha256=output_hash, size_bytes=len(output),
                width=WIDTH, height=HEIGHT, renderer_version=renderer_version,
                accessibility_json=accessibility, created_by=actor,
            )
    except IntegrityError as exc:
        raise DomainError("VERSION_CONFLICT", "La figura ya existe o tuvo un cambio concurrente") from exc
    return {"figure": _figure_data(figure), "version": _version_data(version),
            "created": True, "idempotent": False}


def _figure_data(figure):
    latest = figure.versions.order_by("-version_no").first()
    return {"id": str(figure.id), "table_version_id": str(figure.table_version_id), "name": figure.name,
            "latest_version": latest.version_no if latest else None, "created_by_id": figure.created_by_id,
            "created_at": figure.created_at.isoformat()}


def _scoped_figure(actor, project_id, dataset_id, figure_id):
    project = require_project(actor, project_id)
    figure = ResearchFigure.objects.filter(
        pk=figure_id, table_version__recipe__dataset_version__dataset__project=project,
        table_version__recipe__dataset_version__dataset_id=dataset_id,
    ).select_related("table_version").first()
    if figure is None:
        raise DomainError("NOT_FOUND", "Figura no encontrada")
    return figure


def list_figures(actor, project_id, dataset_id, recipe_id, table_version_no):
    project = require_project(actor, project_id)
    rows = ResearchFigure.objects.filter(
        table_version__recipe_id=recipe_id, table_version__recipe__dataset_version__dataset__project=project,
        table_version__recipe__dataset_version__dataset_id=dataset_id,
        table_version__version_no=table_version_no,
    ).prefetch_related("versions")
    return {"figures": [_figure_data(item) for item in rows]}


def list_figure_versions(actor, project_id, dataset_id, figure_id):
    figure = _scoped_figure(actor, project_id, dataset_id, figure_id)
    return {"figure": _figure_data(figure),
            "versions": [_version_data(v) for v in figure.versions.order_by("-version_no")]}


def get_figure_version(actor, project_id, dataset_id, figure_id, version_no):
    figure = _scoped_figure(actor, project_id, dataset_id, figure_id)
    version = figure.versions.filter(version_no=version_no).first()
    if version is None:
        raise DomainError("NOT_FOUND", "Versión de figura no encontrada")
    if _sha(_canonical(version.spec_json)) != version.spec_sha256:
        raise DomainError("OUTPUT_INVALID", "El hash de especificación de la figura no coincide")
    return {"figure": _figure_data(figure), "version": _version_data(version)}


def get_figure_preview(actor, project_id, dataset_id, figure_id, version_no):
    version_data = get_figure_version(actor, project_id, dataset_id, figure_id, version_no)["version"]
    version = ResearchFigureVersion.objects.select_related("figure").get(pk=version_data["id"])
    root = Path(settings.MEDIA_ROOT).resolve()
    path = (root / version.storage_key).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise DomainError("OUTPUT_INVALID", "El archivo PNG versionado no está disponible")
    data = path.read_bytes()
    if len(data) != version.size_bytes or _sha(data) != version.output_sha256:
        raise DomainError("OUTPUT_INVALID", "El hash del PNG almacenado no coincide")
    return path
