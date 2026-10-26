# ==============================================================================
# FILE: backend/ai/literature_service.py
# PURPOSE: Medical literature service alias in ai package.
# ==============================================================================

from apps.assistant.services.literature_service import (
    search_medical_literature,
    pubmed_service,
    PubMedService,
)

__all__ = [
    "search_medical_literature",
    "pubmed_service",
    "PubMedService",
]
