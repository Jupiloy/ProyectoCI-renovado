"""Importaciones públicas de los modelos Django de TesisMCP."""

from .accounts import UserManager, User, McpAccessToken
from .projects import Project, ProjectParticipant
from .research import ResearchProfile, ConsistencyRow, ResearchVariable, ConsistencyRowVariable, VariableDimension, Indicator
from .instruments import Instrument, InstrumentItem, InstrumentItemIndicator
from .chapters import (
    StepProgress, Chapter, ChapterRevision, ChapterDocument, ChapterDocumentRevision,
    ChapterSnapshot, ReviewComment, ReviewEvent,
)
from .workflows import ProjectWorkflow, WorkflowTask, WorkflowDependency, WorkflowPrompt, WorkflowTaskExecution
from .ai_jobs import AIGenerationJob
from .ai_batches import AIGenerationBatch, AIGenerationBatchItem, AIGenerationBatchSynthesis
from .support import ProjectSupportInvitation, SupportInvitationSource, SupportContribution
from .sources import SourceDocument, SourceExcerpt, SourceSegment, SourcePassage, SourceGrobidAnalysis, SourceMetadataCheck, EvidenceLink
from .documents import DocumentJob, ManuscriptDocument, ManuscriptCitation
from .searches import SearchStrategy, SearchExecution, SearchExecutionSource
from .source_duplicates import SourceDuplicateDecision
from .citations import (
    ChapterCitationOccurrence, CitationEvidenceReview,
    CitationReplacementProposal, CitationReplacementDecision,
)
from .integrations import ZoteroConnection
from .research_data import (
    ResearchDataset, ResearchDatasetVersion, ResearchTableRecipe, ResearchTableRecipeVersion,
    ResearchFigure, ResearchFigureVersion,
)

__all__ = [
    "UserManager",
    "User",
    "McpAccessToken",
    "Project",
    "ProjectParticipant",
    "ResearchProfile",
    "ConsistencyRow",
    "ResearchVariable",
    "ConsistencyRowVariable",
    "VariableDimension",
    "Indicator",
    "Instrument",
    "InstrumentItem",
    "InstrumentItemIndicator",
    "StepProgress",
    "Chapter",
    "ChapterRevision",
    "ChapterDocument",
    "ChapterDocumentRevision",
    "ChapterSnapshot",
    "ReviewComment",
    "ReviewEvent",
    "ProjectWorkflow",
    "WorkflowTask",
    "WorkflowDependency",
    "WorkflowPrompt",
    "WorkflowTaskExecution",
    "AIGenerationJob",
    "AIGenerationBatch",
    "AIGenerationBatchItem",
    "AIGenerationBatchSynthesis",
    "ProjectSupportInvitation",
    "SupportInvitationSource",
    "SupportContribution",
    "SourceDocument",
    "SourceExcerpt",
    "SourceSegment",
    "SourcePassage",
    "SourceGrobidAnalysis",
    "SourceMetadataCheck",
    "EvidenceLink",
    "DocumentJob",
    "ManuscriptDocument",
    "ManuscriptCitation",
    "SearchStrategy",
    "SearchExecution",
    "SearchExecutionSource",
    "SourceDuplicateDecision",
    "ChapterCitationOccurrence",
    "CitationEvidenceReview",
    "CitationReplacementProposal",
    "CitationReplacementDecision",
    "ZoteroConnection",
    "ResearchDataset",
    "ResearchDatasetVersion",
    "ResearchTableRecipe",
    "ResearchTableRecipeVersion",
    "ResearchFigure",
    "ResearchFigureVersion",
]
