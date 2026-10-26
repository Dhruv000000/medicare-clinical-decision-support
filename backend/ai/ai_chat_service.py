# ==============================================================================
# FILE: backend/ai/ai_chat_service.py
# PURPOSE: AI chatbot service boundary for clinical decision support.
# ==============================================================================

from apps.assistant.services.ai_chat_service import (
    chat_with_clinical_ai,
    rag_assistant_engine,
    get_llm_provider,
    GeminiProvider,
    OpenAIProvider,
    build_grounded_clinical_prompt,
)
from ai.rag_service import answer_with_evidence

__all__ = [
    "chat_with_clinical_ai",
    "answer_with_evidence",
    "rag_assistant_engine",
    "get_llm_provider",
    "GeminiProvider",
    "OpenAIProvider",
    "build_grounded_clinical_prompt",
]
