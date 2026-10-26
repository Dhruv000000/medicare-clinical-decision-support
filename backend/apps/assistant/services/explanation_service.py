# ==============================================================================
# FILE: backend/apps/assistant/services/explanation_service.py
# PURPOSE: Re-export alias for clinical explanation service within apps.assistant.
# ==============================================================================

from ai.explanation_service import generate_clinical_explanation
from .llm_provider import build_grounded_clinical_prompt, get_llm_provider, GeminiProvider, OpenAIProvider

__all__ = [
    "generate_clinical_explanation",
    "build_grounded_clinical_prompt",
    "get_llm_provider",
    "GeminiProvider",
    "OpenAIProvider",
]
