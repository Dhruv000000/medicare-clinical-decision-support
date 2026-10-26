# ==============================================================================
# FILE: backend/apps/predictions/services/shap_explainer.py
# PURPOSE: Counterfactual feature attribution engine computing additive symptom risk contributions.
# VIVA EXPLANATION: This module implements an analytical marginal contribution explainer. It measures how much the predicted disease probability shifts when each symptom is counterfactually toggled off, providing local interpretability consistent with Shapley attribution principles.
# ==============================================================================

from typing import List, Dict, Any
from .disease_engine import DISEASE_PROFILES, predict_diseases


# --- explain_prediction ---
# What it does: Computes normalized marginal contributions and risk directions (increases/decreases risk) for present symptoms.
# Why it's structured this way: Uses counterfactual ablation of each symptom against the baseline prior to reveal feature importance.
# Parameters & Returns: feature_vector (Dict[str, int]), top_disease (str) -> List of feature attribution dictionaries.
# ------------------------------------------------------------------------------
def explain_prediction(feature_vector: Dict[str, int], top_disease: str) -> List[Dict[str, Any]]:
    """
    Generates feature contribution (SHAP-style) values for the top predicted disease.
    Matches the schema:
    {
        "feature": "fever",
        "contribution": 0.38,
        "direction": "increases_risk",
        "baseline": 0.05
    }
    """
    profile = DISEASE_PROFILES.get(top_disease)
    baseline_prior = profile["prior"] if profile else 0.10

    # Base prediction with full feature vector
    base_res = predict_diseases(feature_vector)
    base_prob = base_res["top_prediction"]["probability"]

    present_symptoms = [sym for sym, val in feature_vector.items() if val > 0]
    raw_contributions = {}

    if not present_symptoms:
        return []

    # Calculate marginal impact by counterfactually removing each symptom
    for sym in present_symptoms:
        counterfactual_vector = dict(feature_vector)
        counterfactual_vector[sym] = 0

        cf_res = predict_diseases(counterfactual_vector)
        # Find probability of top_disease in counterfactual
        cf_prob = next(
            (item["probability"] for item in cf_res["ranked_diagnoses"] if item["disease"] == top_disease),
            baseline_prior,
        )

        marginal = base_prob - cf_prob
        raw_contributions[sym] = marginal

    # Total marginal difference from baseline
    total_raw = sum(abs(v) for v in raw_contributions.values())
    total_delta = max(0.01, base_prob - baseline_prior)

    explanations = []
    for sym, marginal in raw_contributions.items():
        if total_raw > 0:
            normalized_contrib = (marginal / total_raw) * total_delta
        else:
            normalized_contrib = 0.0

        contrib_val = round(normalized_contrib, 4)
        direction = "increases_risk" if contrib_val >= 0 else "decreases_risk"

        importance_str = f"{'+' if contrib_val >= 0 else ''}{contrib_val:.2f}"
        val_str = "Present" if feature_vector.get(sym, 0) > 0 else "Absent"

        explanations.append({
            "feature": sym,
            "importance": importance_str,
            "value": val_str,
            "contribution": abs(contrib_val),
            "direction": direction,
            "baseline": round(baseline_prior, 4),
        })

    # Sort descending by absolute contribution magnitude
    explanations.sort(key=lambda x: x["contribution"], reverse=True)
    return explanations
