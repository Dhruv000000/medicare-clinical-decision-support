# ==============================================================================
# FILE: backend/ai/nlp_service.py
# PURPOSE: Clinical NLP service for symptom extraction, negation scoping, and vocabulary canonicalization.
# VIVA EXPLANATION: This service processes patient-reported free text narratives using clinical NLP techniques. It handles bounded negation windows (e.g., 'denies headache, has severe fever') so negated symptoms are excluded from ML features, and uses fuzzy string matching to map colloquial phrasing into canonical medical concepts.
# ==============================================================================

import json
import logging
import re
from typing import List, Dict, Any, Union, Optional, Set
from ai.preprocessing import get_preprocessor_v2

logger = logging.getLogger(__name__)


# --- normalize_symptoms ---
# What it does: Extracts and canonicalizes positively asserted symptoms from unstructured text narratives.
# Why it's structured this way: Filters out negated and unmapped tokens to produce a clean list of canonical symptom identifiers for ML inference.
# Parameters & Returns: text (Union[str, List[str]]) -> List of canonical symptom keys (e.g. ['fever', 'cough']).
# ------------------------------------------------------------------------------
def normalize_symptoms(text: Union[str, List[str]]) -> List[str]:
    """
    Extracts and canonicalizes positive clinical symptoms from unstructured text.

    Purpose:
        Applies clinical NLP parsing and negation filtering, returning only
        positively affirmed symptoms mapped to canonical dictionary keys.

    Input Parameters:
        - text (str | list[str]): Free-text clinical narrative or comma-separated symptoms.

    Expected Output:
        List of canonical symptom keys (e.g., ["fever", "cough", "fatigue"]).
    """
    preprocessor = get_preprocessor_v2()
    result = preprocessor.parse_symptoms(text)
    return result["canonical_symptoms"]


# --- parse_clinical_text ---
# What it does: Performs complete clinical NLP parsing returning canonical, negated, and unmapped tokens.
# Why it's structured this way: Exposes complete linguistic decomposition for detailed symptom analysis APIs and doctor review.
# Parameters & Returns: text (str) -> Dict containing canonical_symptoms, negated_symptoms, symptom_vector, and unmapped_tokens.
# ------------------------------------------------------------------------------
def parse_clinical_text(text: str) -> Dict[str, Any]:
    """
    Performs full clinical NLP analysis on patient narrative text.

    Returns:
        Dictionary with 'canonical_symptoms', 'negated_symptoms', and 'unmapped_tokens'.
    """
    preprocessor = get_preprocessor_v2()
    return preprocessor.parse_symptoms(text)


def get_canonical_154_symptom_keys() -> List[str]:
    """Returns the list of 154 canonical symptom features defined in the model schema."""
    try:
        prep = get_preprocessor_v2()
        keys = [k for k in prep.feature_order if prep.features_spec.get(k, {}).get("category") == "symptom"]
        if keys:
            return keys
        return list(prep.feature_order[:154])
    except Exception:
        from ai.preprocessing import CANONICAL_SYMPTOMS
        return list(CANONICAL_SYMPTOMS)[:154]


def validate_symptom_extraction_schema(data: Any, allowed_keys: Set[str]) -> List[str]:
    """
    Validates JSON object against the symptom extraction JSON schema:
    {
        "type": "object",
        "properties": {
            "symptoms": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["symptoms"]
    }
    Strictly filters extracted items to valid keys in allowed_keys.
    """
    if not isinstance(data, dict):
        raise ValueError("Root JSON payload must be an object/dict")
    if "symptoms" not in data:
        raise ValueError("Missing required schema field 'symptoms'")
    if not isinstance(data["symptoms"], list):
        raise ValueError("Field 'symptoms' must be an array/list")

    validated: List[str] = []
    for item in data["symptoms"]:
        if isinstance(item, str):
            clean_item = item.strip().lower()
            if clean_item in allowed_keys and clean_item not in validated:
                validated.append(clean_item)
    return validated


# --- extract_symptoms_via_llm_fallback ---
# What it does: Fallback to structured semantic extraction using lightweight LLM + JSON schema validation.
# Why it's structured this way: When rule-based regex / synonym lookup extracts fewer than 2 symptoms from non-empty text,
# this fallback maps conversational narratives directly to canonical symptom keys.
# ------------------------------------------------------------------------------
def extract_symptoms_via_llm_fallback(
    text: str,
    allowed_keys: Optional[List[str]] = None,
) -> List[str]:
    """
    Fallback Structured Semantic Extraction:
    If rule-based regex and synonym lookup extract fewer than 2 symptoms from non-empty user text input,
    invokes a lightweight LLM extraction fallback that maps conversational narrative directly to
    the 154 CANONICAL_SYMPTOMS keys using JSON schema validation.
    """
    if not text or not str(text).strip():
        return []

    clean_input = str(text).strip()
    if allowed_keys is None:
        allowed_keys = get_canonical_154_symptom_keys()
    allowed_set = set(allowed_keys)

    # 1. Attempt LLM-based structured JSON extraction if provider is configured
    try:
        from apps.assistant.services.llm_provider import get_llm_provider
        provider = get_llm_provider()
        if hasattr(provider, "is_configured") and provider.is_configured:
            prompt = (
                f"You are a clinical NLP symptom extraction engine. Analyze the patient narrative:\n"
                f"\"{clean_input}\"\n\n"
                f"Task: Extract only positively affirmed symptoms and map them strictly to keys from the allowed 154 canonical vocabulary.\n"
                f"Allowed Keys:\n{json.dumps(list(allowed_keys))}\n\n"
                f"Instructions:\n"
                f"- Exclude negated symptoms (e.g. 'no fever', 'denies headache').\n"
                f"- Return ONLY a JSON object adhering to this schema: {{\"symptoms\": [\"key1\", \"key2\"]}}\n"
                f"- Do not include any explanations, markdown fences, or text outside the JSON."
            )
            llm_result = provider.generate_response(prompt=prompt, citations=[])
            raw_response = llm_result.get("response", "")

            # Extract JSON block
            json_match = re.search(r"\{.*\}", raw_response, flags=re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                validated = validate_symptom_extraction_schema(parsed, allowed_set)
                if validated:
                    logger.info("LLM semantic extraction fallback identified symptoms: %s", validated)
                    return validated
    except Exception as exc:
        logger.warning("LLM symptom extraction failed or timed out: %s; using semantic extractive fallback.", exc)

    # 2. Intelligent semantic / anatomical keyphrase fallback when offline or LLM unavailable
    semantic_mappings: Dict[str, List[str]] = {
        # Abdominal & surgical
        r"\b(lower right|right lower|rlq|belly button|navel|radiating to right)\b": ["abdominal_pain"],
        r"\b(rebound|tenderness|guarding|appendix)\b": ["abdominal_pain"],
        r"\b(stomach (hurts|cramp|ache)|tummy pain)\b": ["abdominal_pain"],
        # Dermatology
        r"\b(silvery|scales|flaking|scaly|plaque)\b": ["skin_peeling", "skin_rash"],
        r"\b(red (patches|bumps|spots)|hives|rash|welts)\b": ["skin_rash", "erythema"],
        r"\b(itchy|itching|scratching)\b": ["itching"],
        # Neurological
        r"\b(droop(ing)?|crooked mouth|one side of face|unable to close eye)\b": ["facial_droop"],
        r"\b(headache|head throbbing|head pounding|migraine)\b": ["headache"],
        r"\b(dizzy|lightheaded|room spinning|vertigo)\b": ["dizziness", "vertigo"],
        # Musculoskeletal
        r"\b(big toe|gout|toe pain|hot joint|swollen toe)\b": ["joint_pain", "joint_swelling"],
        r"\b(joint (stiff|swollen|burning|aching)|morning stiffness)\b": ["joint_pain", "morning_stiffness"],
        # Systemic & infectious
        r"\b(cyclical fever|burning up|high temp|feverish)\b": ["fever"],
        r"\b(shiver(ing)?|chills|shaking with cold|rigors)\b": ["chills"],
        r"\b(sweating|profuse sweat|drenched in sweat)\b": ["excessive_sweating"],
        r"\b(muscle (pain|ache)|myalgia|body (ache|pain)|sore all over)\b": ["body_aches", "myalgia"],
        # Respiratory
        r"\b(short of breath|can't breathe|breathless|gasping|air hunger)\b": ["dyspnea"],
        r"\b(cough(ing)?|hack(ing)?)\b": ["cough"],
        r"\b(sore throat|throat hurts|painful swallowing)\b": ["sore_throat"],
        # Metabolic / Endocrine
        r"\b(peeing (a lot|constantly)|frequent urination|lots of urine)\b": ["polyuria"],
        r"\b(constant thirst|unquenchable thirst|drinking water all day)\b": ["polydipsia"],
        r"\b(lost weight without trying|unexplained weight loss)\b": ["weight_loss"],
        r"\b(exhausted|no energy|chronic fatigue|wipe(d)? out)\b": ["fatigue"],
    }

    lowered = clean_input.lower()
    extracted_fallback: List[str] = []
    for pattern, sym_keys in semantic_mappings.items():
        if re.search(pattern, lowered):
            for k in sym_keys:
                if k in allowed_set and k not in extracted_fallback:
                    extracted_fallback.append(k)

    # Validate output through standard schema validator
    return validate_symptom_extraction_schema({"symptoms": extracted_fallback}, allowed_set)
