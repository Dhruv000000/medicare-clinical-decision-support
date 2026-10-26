# ==============================================================================
# FILE: backend/apps/predictions/services/__init__.py
# PURPOSE: Package initializer exposing prediction workflows, disease engines, TreeSHAP explainers, and symptom parsers.
# VIVA EXPLANATION: Exports unified service layer interfaces for disease prediction, TreeSHAP feature attributions, and symptom NLP canonicalization across views.
# ==============================================================================


from .symptom_parser import (
    parse_symptoms,
    get_canonical_symptom_catalog,
    suggest_related_symptoms,
    CANONICAL_SYMPTOMS,
    SYMPTOM_SYNONYMS,
)
from .disease_engine import (
    predict_diseases,
    DISEASE_PROFILES,
)
from .shap_explainer import explain_prediction
from .prediction_service import (
    execute_clinical_prediction_workflow,
    execute_symptom_analysis_workflow,
)

__all__ = [
    "parse_symptoms",
    "get_canonical_symptom_catalog",
    "suggest_related_symptoms",
    "predict_diseases",
    "explain_prediction",
    "execute_clinical_prediction_workflow",
    "execute_symptom_analysis_workflow",
    "CANONICAL_SYMPTOMS",
    "SYMPTOM_SYNONYMS",
    "DISEASE_PROFILES",
]
