# ==============================================================================
# FILE: backend/apps/assistant/services/ai_chat_service.py
# PURPOSE: High-level AI chatbot service orchestrating prediction-grounded clinical dialogues.
# VIVA EXPLANATION: Implements the Facade design pattern wrapping RAG retrieval,
# electronic health record context, and live LLM inference.
# ==============================================================================

import logging
from typing import Dict, Any, Optional, Union, List

from .rag_engine import rag_assistant_engine, RAGAssistantEngine
from .llm_provider import get_llm_provider, GeminiProvider, OpenAIProvider, build_grounded_clinical_prompt
from .triage_service import triage_service, EmergencyTriageService, detect_emergency

logger = logging.getLogger(__name__)


def chat_with_clinical_ai(
    prompt: str,
    user=None,
    patient_user=None,
    conversation_id: Optional[int] = None,
    limit_citations: int = 3,
    user_symptoms_text: Optional[str] = None,
    top_predicted_disease: Optional[str] = None,
    confidence: Optional[Union[float, str]] = None,
    shap_drivers: Optional[Union[str, List[str]]] = None,
    prediction_id: Optional[int] = None,
    prediction_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Executes a clinical chatbot conversation grounded in disease predictions and PubMed evidence.

    Raises:
        ValueError / RuntimeError: Propagates live LLM provider or configuration errors
        rather than returning canned placeholder text.
    """
    return rag_assistant_engine.process_chat(
        user=user,
        prompt=prompt,
        patient_user=patient_user,
        conversation_id=conversation_id,
        limit_citations=limit_citations,
        user_symptoms_text=user_symptoms_text,
        top_predicted_disease=top_predicted_disease,
        confidence=confidence,
        shap_drivers=shap_drivers,
        prediction_id=prediction_id,
        prediction_context=prediction_context,
    )


__all__ = [
    "chat_with_clinical_ai",
    "rag_assistant_engine",
    "RAGAssistantEngine",
    "triage_service",
    "EmergencyTriageService",
    "detect_emergency",
    "get_llm_provider",
    "GeminiProvider",
    "OpenAIProvider",
    "build_grounded_clinical_prompt",
]
