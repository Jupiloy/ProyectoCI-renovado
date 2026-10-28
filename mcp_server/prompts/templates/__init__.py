"""Agregador central de plantillas de prompts metodológicos (Capítulos 1 al 7: P01 a P32)."""

from typing import Any

from mcp_server.prompts.templates.chapter_1 import CHAPTER_1_TEMPLATES
from mcp_server.prompts.templates.chapter_2 import CHAPTER_2_TEMPLATES
from mcp_server.prompts.templates.chapter_3 import CHAPTER_3_TEMPLATES
from mcp_server.prompts.templates.chapter_4 import CHAPTER_4_TEMPLATES
from mcp_server.prompts.templates.chapter_5 import CHAPTER_5_TEMPLATES
from mcp_server.prompts.templates.chapter_6 import CHAPTER_6_TEMPLATES
from mcp_server.prompts.templates.chapter_7 import CHAPTER_7_TEMPLATES

TEMPLATES_POR_PASO: dict[str, dict[str, Any]] = {
    **CHAPTER_1_TEMPLATES,
    **CHAPTER_2_TEMPLATES,
    **CHAPTER_3_TEMPLATES,
    **CHAPTER_4_TEMPLATES,
    **CHAPTER_5_TEMPLATES,
    **CHAPTER_6_TEMPLATES,
    **CHAPTER_7_TEMPLATES,
}

__all__ = ["TEMPLATES_POR_PASO"]
