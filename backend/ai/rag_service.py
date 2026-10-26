# ==============================================================================
# FILE: backend/ai/rag_service.py
# PURPOSE: Retrieval-Augmented Generation (RAG) boundary synthesizing evidence-based clinical answers.
# VIVA EXPLANATION: This service demonstrates modern Clinical AI by combining real-time PubMed biomedical literature retrieval with large language model synthesis. It grounds clinical responses in peer-reviewed citations to prevent hallucinations and attaches mandatory regulatory safety disclaimers.
# ==============================================================================

from typing import Dict, Any, Optional, Union, List
from apps.assistant.services.rag_engine import rag_assistant_engine, MANDATORY_REGULATORY_DISCLAIMER
from apps.assistant.services.pubmed_service import pubmed_service
from apps.assistant.services.llm_provider import get_llm_provider


# --- answer_with_evidence ---
# What it does: Retrieves PubMed peer-reviewed research citations and generates evidence-grounded answers with patient context and disease prediction grounding.
# Why it's structured this way: Follows the RAG architecture pattern (Retrieve -> Augment -> Generate) ensuring answers cite verified PMIDs and align with the diagnostic model.
# Parameters & Returns: question (str), patient_user (Optional), limit_citations (int) -> Dict with query, response, citations, disclaimer.
# ------------------------------------------------------------------------------
def answer_with_evidence(
    question: str,
    patient_user=None,
    limit_citations: int = 3,
    user_symptoms_text: Optional[str] = None,
    top_predicted_disease: Optional[str] = None,
    confidence: Optional[Union[float, str]] = None,
    shap_drivers: Optional[Union[str, List[str]]] = None,
    prediction_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Synthesizes an evidence-grounded clinical response for a clinical question.
    Can be used standalone or within authenticated user sessions.
    """
    clean_q = question.strip()
    if not clean_q:
        return {
            "query": "",
            "response": "Clinical question cannot be empty.",
            "citations": [],
            "disclaimer": MANDATORY_REGULATORY_DISCLAIMER,
            "status": "empty",
        }

    # 1. Patient Context
    patient_context = rag_assistant_engine._build_patient_context(patient_user) if patient_user else ""

    # 2. Literature Retrieval via Clinical Keywords
    search_keywords = rag_assistant_engine.extract_clinical_keywords(clean_q, patient_context)
    pubmed_res = pubmed_service.search_pubmed(search_keywords, limit=limit_citations, fetch_abstracts=True)
    citations = pubmed_res.get("citations", [])

    # 3. LLM Generation Grounded in Prediction
    llm_res = get_llm_provider().generate_response(
        prompt=clean_q,
        citations=citations,
        patient_context=patient_context,
        user_symptoms_text=user_symptoms_text,
        top_predicted_disease=top_predicted_disease,
        confidence=confidence,
        shap_drivers=shap_drivers,
        prediction_context=prediction_context,
    )

    return {
        "query": clean_q,
        "response": llm_res.get("response", ""),
        "citations": citations,
        "disclaimer": MANDATORY_REGULATORY_DISCLAIMER,
        "provider": llm_res.get("provider", "extractive"),
        "model": llm_res.get("model", "grounded_rules"),
        "grounded": llm_res.get("grounded", bool(citations)),
        "predicted_condition": top_predicted_disease,
        "confidence": confidence,
        "status": "success" if citations else "no_results",
    }

