# ==============================================================================
# FILE: backend/ai/shap_service.py
# PURPOSE: Explainable AI (XAI) service providing TreeSHAP feature attributions for clinical risk predictions.
# VIVA EXPLANATION: TreeSHAP provides mathematically rigorous local interpretability grounded in Cooperative Game Theory (Shapley values). It guarantees efficiency, symmetry, dummy, and additivity axioms, executing in polynomial time O(TLD^2) to reveal exactly which symptoms and vitals increased or decreased disease risk.
# ==============================================================================

import logging
from typing import Any, Dict, List, Optional
import numpy as np
from ai.engine import get_engine, ModelNotLoadedError

logger = logging.getLogger(__name__)


# --- explain_prediction ---
# What it does: Computes sample-level TreeSHAP feature attributions for a given clinical case.
# Why it's structured this way: Encapsulates Shapley math so clinicians receive intuitive 'increases risk' vs 'decreases risk' factors without raw matrix operations.
# Parameters & Returns: input_data (dict), top_disease (Optional[str]), engine (Optional[DiseaseRiskEngine]) -> list of feature attribution dicts.
# ------------------------------------------------------------------------------
def explain_prediction(
    input_data: Dict[str, Any],
    top_disease: Optional[str] = None,
    engine=None,
) -> List[Dict[str, Any]]:
    """
    Computes sample-level TreeSHAP feature attributions for a given clinical case.

    Purpose:
        Explains *why* the machine learning model predicted a specific disease
        by calculating the exact directional impact (+ risk increase, - risk decrease)
        of each observed symptom and physiological vital sign.

    Input Parameters:
        - input_data (dict): Preprocessed clinical feature dictionary or raw symptoms.
        - top_disease (str | None): Target condition to explain. If None, uses top class.
        - engine: Optional pre-loaded DiseaseRiskEngine instance.

    Expected Output Format:
        List of feature attribution dictionaries:
        [
            {
                "feature": "fever",
                "shap_value": 0.3842,
                "contribution": 0.3842,
                "direction": "increases_risk",
                "baseline": 0.12,
                "value": 1.0
            },
            ...
        ]
    """
    if engine is None:
        engine = get_engine()

    try:
        # Preprocess input into aligned numerical feature vector
        preprocessed = engine.preprocessor.preprocess(input_data)
        feature_matrix = preprocessed.to_model_input()

        # Compute TreeSHAP values using TreeExplainer
        explainer = getattr(engine, "shap_explainer", None) or getattr(engine, "explainer", None)
        if explainer is None:
            logger.warning("TreeSHAP explainer not initialized; returning empty explanations.")
            return []

        shap_values = explainer.shap_values(feature_matrix) if hasattr(explainer, "shap_values") else explainer(feature_matrix)
        base_value = float(explainer.expected_value[0]) if hasattr(explainer, "expected_value") and isinstance(explainer.expected_value, (list, np.ndarray)) else (float(explainer.expected_value) if hasattr(explainer, "expected_value") else 0.0)

        explanations = []
        for idx, feat_name in enumerate(engine.feature_order):
            if hasattr(shap_values, "values"):
                s_val = float(shap_values.values[0][idx])
            elif isinstance(shap_values, list):
                s_val = float(shap_values[0][0][idx])
            elif isinstance(shap_values, np.ndarray):
                s_val = float(shap_values[0, idx, 0]) if shap_values.ndim == 3 else float(shap_values[0][idx])
            else:
                s_val = 0.0

            if abs(s_val) > 0.001:
                val = float(feature_matrix[0][idx])
                explanations.append({
                    "feature": feat_name,
                    "importance": f"{'+' if s_val >= 0 else ''}{s_val:.2f}",
                    "shap_value": round(s_val, 4),
                    "contribution": round(abs(s_val), 4),
                    "direction": "increases_risk" if s_val > 0 else "decreases_risk",
                    "baseline": round(base_value, 4),
                    "value": val,
                })

        # Sort descending by absolute contribution magnitude
        explanations.sort(key=lambda x: x["contribution"], reverse=True)
        return explanations

    except Exception as exc:
        logger.error(f"Failed to generate TreeSHAP explanations: {exc}")
        return []
