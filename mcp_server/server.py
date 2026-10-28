"""
Servidor MCP para TesisMCP.

Este archivo inicializa el servidor MCP utilizando el SDK oficial `mcp` (versión 2.x con `MCPServer`).
Expone el catálogo metodológico y las herramientas conectadas al backend.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.mcpserver import MCPServer
from mcp_server.django_bridge import setup_django
from mcp_server.project_tools import register_project_tools
from mcp_server.prompts import register_project_prompts

setup_django()
from thesis.step_catalogue import CATALOGO_PASOS

# 1. Inicialización del servidor MCP
# Le damos un nombre descriptivo al servidor que identificará al servicio ante el cliente LLM.
app = MCPServer(
    name="TesisMCP",
    description="Servidor MCP para la asistencia metodológica y supervisión de tesis universitarias."
)

# 2. Catálogo compartido de pasos metodológicos (Capítulos 1 al 7: P01 a P32)

CATALOGO_MVP = CATALOGO_PASOS


# 3. Herramientas MCP (@app.tool)
# Las funciones decoradas con @app.tool se publican automáticamente como herramientas que el LLM puede ejecutar.
# El docstring y los tipos de parámetros le indican a la IA para qué sirve la herramienta y qué datos debe pasar.

@app.tool()
def estado_servidor() -> Dict[str, Any]:
    """
    Retorna el estado del servidor TesisMCP, su versión y las capacidades activas.
    Útil para comprobar que la conexión entre el cliente LLM y el servidor MCP está activa.
    """
    return {
        "estado": "ACTIVO",
        "servidor": "TesisMCP",
        "version": "0.3.0",
        "fase": "Capítulos 1 al 7 (P01 a P32 Habilitados)",
        "capitulos_disponibles": [1, 2, 3, 4, 5, 6, 7],
        "total_pasos": len(CATALOGO_PASOS),
        "motor_prompts": "ACTIVO (32 pasos P01-P32 + 3 prompts de rol)",
        "total_prompts": 35,
        "transporte_soportado": ["stdio"]
    }


@app.tool()
def listar_pasos_mvp(capitulo: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Lista los pasos metodológicos del catálogo (P01 al P32).
    
    Args:
        capitulo: Filtro opcional por número de capítulo (1 al 7). Si no se especifica, lista todos los 32 pasos.
    """
    resultado = []
    for codigo, info in CATALOGO_PASOS.items():
        if capitulo is None or info["capitulo"] == capitulo:
            resultado.append({
                "codigo": codigo,
                "capitulo": info["capitulo"],
                "nombre": info["nombre"],
                "objetivo": info["objetivo"]
            })
    return resultado


@app.tool()
def consultar_detalle_paso(step_code: str) -> Dict[str, Any]:
    """
    Obtiene el detalle completo, objetivo y campos de entrada necesarios para ejecutar un paso (P01 a P32).
    
    Args:
        step_code: Código del paso (ejemplo: 'P01', 'P04', 'P09', 'P12', 'P30').
    """
    codigo_limpio = step_code.strip().upper()
    if codigo_limpio not in CATALOGO_PASOS:
        return {
            "error": True,
            "mensaje": f"El paso '{step_code}' no existe en el catálogo metodológico (pasos válidos: P01 a P32)."
        }
    
    info = CATALOGO_PASOS[codigo_limpio]
    return {
        "error": False,
        "codigo": codigo_limpio,
        "capitulo": info["capitulo"],
        "nombre": info["nombre"],
        "objetivo": info["objetivo"],
        "entradas_requeridas": info["entradas_requeridas"]
    }


# 4. Herramientas conectadas a Django y PostgreSQL
register_project_tools(app)

# 5. Prompts metodológicos y roles secuenciales del cliente LLM
register_project_prompts(app)


# 6. Punto de entrada para ejecución por stdio
# Cuando Claude Desktop o Cursor ejecutan `python -m mcp_server.server`, se utiliza el transporte estándar stdio.
if __name__ == "__main__":
    app.run()
