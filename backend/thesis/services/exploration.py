from thesis.integrations.openalex import search_works
from thesis.services.projects import get_project_state


GUIDANCE_QUESTIONS = [
    "¿Qué área o situación te interesa investigar?",
    "¿A qué población o institución podrías acceder?",
    "¿En qué lugar y periodo observarías el problema?",
]


def explore_idea(actor, project_id, *, search_provider=search_works) -> dict:
    state = get_project_state(actor, project_id)
    idea = state["idea_provisional"]
    if not idea:
        return {
            "project_id": state["project_id"],
            "search_status": "NEEDS_IDEA",
            "guidance_questions": GUIDANCE_QUESTIONS,
            "works": [],
            "notice": "Todavía no hay una idea provisional. Las preguntas ayudan a iniciar la exploración.",
        }
    works = search_provider(idea)
    return {
        "project_id": state["project_id"],
        "search_status": "RESULTS" if works else "NO_RESULTS",
        "guidance_questions": [],
        "works": works,
        "notice": (
            "Estos registros proceden de metadatos de OpenAlex. No se ha leído su texto completo "
            "ni se ha demostrado que describan el problema local."
        ),
    }
