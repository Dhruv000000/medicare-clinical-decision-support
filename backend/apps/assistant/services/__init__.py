# ==============================================================================
# FILE: backend/apps/assistant/services/__init__.py
# PURPOSE: Package initializer exposing PubMed retrieval and clinical RAG assistant services.
# VIVA EXPLANATION: Exports PubMedService and RAGAssistantEngine singletons for literature synthesis across application views.
# ==============================================================================

from .pubmed_service import PubMedService, pubmed_service
from .rag_engine import RAGAssistantEngine, rag_assistant_engine
from .triage_service import EmergencyTriageService, triage_service, detect_emergency

__all__ = [
    "PubMedService",
    "pubmed_service",
    "RAGAssistantEngine",
    "rag_assistant_engine",
    "EmergencyTriageService",
    "triage_service",
    "detect_emergency",
]
