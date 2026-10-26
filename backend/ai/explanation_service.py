# ==============================================================================
# FILE: backend/ai/explanation_service.py
# PURPOSE: Clinical decision support explanation service grounded in ML predictions.
# VIVA EXPLANATION: Implements the clinical explanation engine for MediCare CDSS.
# Formats patient symptoms, top predicted disease, confidence score, and TreeSHAP
# attribution drivers into a clinical prompt, queries the live LLM provider
# (Gemini or OpenAI), and generates precise, actionable clinical impressions and
# next steps while forbidding canned placeholder fallbacks.
# ==============================================================================

import logging
import os
from typing import Dict, Any, List, Optional, Union

from apps.assistant.services.llm_provider import (
    get_llm_provider,
    build_grounded_clinical_prompt,
    GeminiProvider,
    OpenAIProvider,
    BaseLLMProvider,
)

logger = logging.getLogger(__name__)


# --- generate_clinical_explanation ---
# What it does: Produces a high-precision clinical explanation directly grounded
# in the patient complaint, top predicted disease, confidence%, and SHAP drivers.
# Why it's structured this way: Fulfills the strict 3-tier clinical response:
# 1. Primary Clinical Impression (why symptoms point to top condition).
# 2. Key Red Flags & Next Steps (urgent clinical signs and recommended tests).
# 3. Actionable clinical guidance (no generic or vague advice).
# Parameters & Returns: Symptoms, top disease, confidence, shap drivers -> Clinical explanation payload.
# ------------------------------------------------------------------------------
def generate_clinical_explanation(
    user_symptoms_text: str,
    top_predicted_disease: str,
    confidence: Union[float, str],
    shap_drivers: Optional[Union[str, List[Union[str, Dict[str, Any]]]]] = None,
    citations: Optional[List[Dict[str, Any]]] = None,
    patient_context: Optional[str] = None,
    prompt: Optional[str] = None,
    provider: Optional[BaseLLMProvider] = None,
) -> Dict[str, Any]:
    """
    Generates a live clinical explanation using the active LLM provider (Gemini or OpenAI).

    Strict Requirements:
    1. Initialized with live environment API keys: os.getenv("GEMINI_API_KEY") or OPENAI_API_KEY.
    2. Zero canned/mock literature fallbacks.
    3. Grounded in user symptoms, top predicted disease, confidence%, and SHAP drivers.
    4. If the API call fails or key is invalid, raises RuntimeError/ValueError rather than silently returning canned text.
    """
    if not user_symptoms_text or not user_symptoms_text.strip():
        raise ValueError("Field 'user_symptoms_text' is required to ground clinical explanation.")

    if not top_predicted_disease or not top_predicted_disease.strip():
        raise ValueError("Field 'top_predicted_disease' is required to ground clinical explanation.")

    llm = provider or get_llm_provider()

    user_query = prompt or f"Explain why the clinical presentation indicates {top_predicted_disease}."

    logger.info(
        "Generating clinical explanation: condition='%s', confidence='%s', provider='%s'",
        top_predicted_disease,
        confidence,
        type(llm).__name__,
    )

    try:
        response_data = llm.generate_response(
            prompt=user_query,
            citations=citations or [],
            patient_context=patient_context or "",
            user_symptoms_text=user_symptoms_text,
            top_predicted_disease=top_predicted_disease,
            confidence=confidence,
            shap_drivers=shap_drivers,
        )
        return response_data
    except (ValueError, RuntimeError) as exc:
        logger.error(
            "Clinical explanation LLM call failed for '%s': %s",
            top_predicted_disease,
            exc,
            exc_info=True,
        )
        raise
