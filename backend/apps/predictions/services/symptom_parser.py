# ==============================================================================
# FILE: backend/apps/predictions/services/symptom_parser.py
# PURPOSE: Clinical symptom NLP extraction, synonym vocabulary canonicalization, and co-occurrence suggestions.
# VIVA EXPLANATION: This module tokenizes raw patient complaint text into canonical medical concepts. It maintains a clinical lexicon mapping hundreds of colloquial expressions to standard symptom identifiers, and provides co-occurring clinical suggestions based on common disease presentations.
# ==============================================================================

import re
from typing import List, Dict, Union, Any

CANONICAL_SYMPTOMS = [
    "fever",
    "cough",
    "fatigue",
    "headache",
    "dyspnea",
    "chest_pain",
    "sore_throat",
    "rhinorrhea",
    "polyuria",
    "polydipsia",
    "dizziness",
    "nausea",
    "photophobia",
    "body_aches",
    "blurred_vision",
    "diarrhea",
    "chills",
    "weight_loss",
    "sweating",
    "excessive_sweating",
    "myalgia",
    "muscle_pain",
    "shivering",
    "high_fever",
    "rigors",
    # Unmapped Specialties
    "scaly_rash",
    "skin_peeling",
    "itching",
    "skin_rash",
    "erythema",
    "facial_droop",
    "facial_palsy",
    "cranial_nerve_deficit",
    "podagra",
    "joint_pain",
    "joint_swelling",
    "acute_appendicitis",
    "rebound_tenderness",
    "right_lower_quadrant_pain",
    "periumbilical_pain",
    "abdominal_pain",
]

SYMPTOM_SYNONYMS: Dict[str, str] = {
    # Fever
    "fever": "fever",
    "high temperature": "fever",
    "feverish": "fever",
    "pyrexia": "fever",
    "temp": "fever",
    "elevated temperature": "fever",
    "burning up": "fever",
    "high cyclical fever": "fever",
    "cyclical fever": "fever",
    "cyclical high fever": "fever",
    "high fever": "fever",
    "spiking fever": "fever",
    # Cough
    "cough": "cough",
    "coughing": "cough",
    "dry cough": "cough",
    "hacking cough": "cough",
    "productive cough": "cough",
    "phlegm": "cough",
    "barking cough": "cough",
    # Fatigue
    "fatigue": "fatigue",
    "tired": "fatigue",
    "tiredness": "fatigue",
    "exhaustion": "fatigue",
    "lethargy": "fatigue",
    "weakness": "fatigue",
    "drowsiness": "fatigue",
    "feeling weak": "fatigue",
    # Headache
    "headache": "headache",
    "head ache": "headache",
    "head hurting": "headache",
    "throbbing headache": "headache",
    "throbbing head": "headache",
    "head is throbbing": "headache",
    "head throbbing": "headache",
    "pain in head": "headache",
    "head pain": "headache",
    "migraine": "headache",
    # Dyspnea / Breathlessness
    "dyspnea": "dyspnea",
    "shortness of breath": "dyspnea",
    "breathless": "dyspnea",
    "breathlessness": "dyspnea",
    "difficulty breathing": "dyspnea",
    "hard to breathe": "dyspnea",
    "wheezing": "dyspnea",
    "wheeze": "dyspnea",
    # Chest Pain
    "chest pain": "chest_pain",
    "chest tightness": "chest_pain",
    "tight chest": "chest_pain",
    "pressure in chest": "chest_pain",
    "chest ache": "chest_pain",
    "angina": "chest_pain",
    "chest discomfort": "chest_pain",
    # Sore Throat
    "sore throat": "sore_throat",
    "throat pain": "sore_throat",
    "scratchy throat": "sore_throat",
    "pain swallowing": "sore_throat",
    "pharyngitis": "sore_throat",
    # Rhinorrhea / Runny nose / Sneezing
    "rhinorrhea": "rhinorrhea",
    "runny nose": "rhinorrhea",
    "sneezing": "rhinorrhea",
    "nasal congestion": "rhinorrhea",
    "stuffy nose": "rhinorrhea",
    "congestion": "rhinorrhea",
    "blocked nose": "rhinorrhea",
    # Polyuria
    "polyuria": "polyuria",
    "frequent urination": "polyuria",
    "peeing often": "polyuria",
    "excessive urination": "polyuria",
    "urinating frequently": "polyuria",
    "peeing constantly": "polyuria",
    # Polydipsia
    "polydipsia": "polydipsia",
    "excessive thirst": "polydipsia",
    "always thirsty": "polydipsia",
    "extreme thirst": "polydipsia",
    "thirsty": "polydipsia",
    # Dizziness
    "dizziness": "dizziness",
    "dizzy": "dizziness",
    "lightheaded": "dizziness",
    "lightheadedness": "dizziness",
    "vertigo": "dizziness",
    "feeling faint": "dizziness",
    # Nausea / Vomiting
    "nausea": "nausea",
    "nauseous": "nausea",
    "vomiting": "nausea",
    "throwing up": "nausea",
    "puking": "nausea",
    "queasy": "nausea",
    "upset stomach": "nausea",
    # Photophobia
    "photophobia": "photophobia",
    "sensitive to light": "photophobia",
    "light sensitivity": "photophobia",
    "eye hurt in light": "photophobia",
    # Body Aches / Myalgia
    "body aches": "body_aches",
    "body ache": "body_aches",
    "muscle pain": "myalgia",
    "myalgia": "myalgia",
    "muscle ache": "myalgia",
    "joint pain": "body_aches",
    "aching body": "body_aches",
    # Blurred Vision
    "blurred vision": "blurred_vision",
    "blurry vision": "blurred_vision",
    "hazy vision": "blurred_vision",
    "fuzzy vision": "blurred_vision",
    # Diarrhea
    "diarrhea": "diarrhea",
    "loose stools": "diarrhea",
    "watery stools": "diarrhea",
    "stomach cramps": "diarrhea",
    # Chills / Rigors / Shivering
    "chills": "chills",
    "shivering chills": "chills",
    "severe shivering chills": "chills",
    "severe chills": "chills",
    "shivering": "chills",
    "shivers": "chills",
    "cold sweats": "chills",
    "rigors": "rigors",
    # Sweating / Diaphoresis
    "sweating": "sweating",
    "profuse sweating": "sweating",
    "sweating profusely": "sweating",
    "excessive sweating": "sweating",
    "heavy sweating": "sweating",
    "diaphoresis": "sweating",
    # Weight Loss
    "weight loss": "weight_loss",
    "losing weight": "weight_loss",
    "unexplained weight loss": "weight_loss",

    # Dermatology: Psoriasis
    "silvery white scales": "scaly_rash",
    "silvery scales": "scaly_rash",
    "white scales": "scaly_rash",
    "scaly rash": "scaly_rash",
    "scaly skin": "scaly_rash",
    "scaly plaques": "scaly_rash",
    "silver scales": "scaly_rash",
    "red patches": "skin_rash",
    "erythematous patches": "skin_rash",
    "red skin patches": "skin_rash",
    "flaking": "skin_peeling",
    "flaking skin": "skin_peeling",
    "flaky skin": "skin_peeling",
    "skin flaking": "skin_peeling",
    "pitted nails": "nail_clubbing",
    "nail pitting": "nail_clubbing",
    "pitting of nails": "nail_clubbing",
    "pitted nail": "nail_clubbing",

    # Neurological: Bell's Palsy & Facial Deficits
    "facial drooping": "facial_droop",
    "facial droop": "facial_droop",
    "face drooping": "facial_droop",
    "drooping face": "facial_droop",
    "mouth drooping": "facial_droop",
    "drooping mouth": "facial_droop",
    "drooping of the face": "facial_droop",
    "unable to close eye": "facial_droop",
    "cannot close eye": "facial_droop",
    "unable to close one eye": "facial_droop",
    "difficulty closing eye": "facial_droop",
    "eye cannot close": "facial_droop",
    "dribbling food": "facial_droop",
    "food dribbling": "facial_droop",
    "drooling food": "facial_droop",
    "dribbling from mouth": "facial_droop",
    "facial palsy": "facial_droop",
    "face palsy": "facial_droop",
    "cranial nerve deficit": "facial_droop",
    "cranial nerve palsy": "facial_droop",
    "bell's palsy": "facial_droop",
    "bells palsy": "facial_droop",

    # Musculoskeletal: Gout & Podagra
    "big toe pain": "podagra",
    "pain in big toe": "podagra",
    "great toe pain": "podagra",
    "pain in great toe": "podagra",
    "swollen big toe": "podagra",
    "podagra": "podagra",
    "joint burning hot": "joint_swelling",
    "burning hot joint": "joint_swelling",
    "hot swollen joint": "joint_swelling",
    "joint hot to touch": "joint_swelling",
    "extreme sensitivity to touch": "joint_swelling",
    "painful to touch": "joint_swelling",
    "cannot touch joint": "joint_swelling",
    "sensitive to touch": "joint_swelling",

    # Abdominal: Appendicitis & RLQ / Rebound Tenderness
    "lower right abdomen": "abdominal_pain",
    "lower right abdominal pain": "abdominal_pain",
    "pain in lower right abdomen": "abdominal_pain",
    "right lower quadrant": "abdominal_pain",
    "right lower quadrant pain": "abdominal_pain",
    "rlq pain": "abdominal_pain",
    "belly button pain radiating to right": "abdominal_pain",
    "pain around belly button radiating to right": "abdominal_pain",
    "periumbilical pain radiating to right": "abdominal_pain",
    "rebound tenderness": "abdominal_pain",
    "rebound pain": "abdominal_pain",
    "mcburney tenderness": "abdominal_pain",
    "mcburney's point": "abdominal_pain",
    "pain worsens when releasing pressure": "abdominal_pain",
    "acute appendicitis": "abdominal_pain",
    "appendicitis": "abdominal_pain",
}

CATALOG_METADATA = [
    {"id": "fever", "label": "Fever / Pyrexia", "category": "General"},
    {"id": "cough", "label": "Cough", "category": "Respiratory"},
    {"id": "fatigue", "label": "Fatigue / Lethargy", "category": "General"},
    {"id": "headache", "label": "Headache / Migraine", "category": "Neurological"},
    {"id": "dyspnea", "label": "Shortness of Breath", "category": "Respiratory"},
    {"id": "chest_pain", "label": "Chest Pain / Tightness", "category": "Cardiovascular"},
    {"id": "sore_throat", "label": "Sore Throat", "category": "ENT"},
    {"id": "rhinorrhea", "label": "Runny Nose / Congestion", "category": "ENT"},
    {"id": "polyuria", "label": "Frequent Urination", "category": "Metabolic / Renal"},
    {"id": "polydipsia", "label": "Excessive Thirst", "category": "Metabolic"},
    {"id": "dizziness", "label": "Dizziness / Lightheadedness", "category": "Neurological"},
    {"id": "nausea", "label": "Nausea / Vomiting", "category": "Gastrointestinal"},
    {"id": "photophobia", "label": "Sensitivity to Light", "category": "Neurological / Optical"},
    {"id": "body_aches", "label": "Muscle & Body Aches", "category": "General"},
    {"id": "blurred_vision", "label": "Blurred Vision", "category": "Optical"},
    {"id": "diarrhea", "label": "Diarrhea / Abdominal Cramps", "category": "Gastrointestinal"},
    {"id": "chills", "label": "Chills / Shivering", "category": "General"},
    {"id": "weight_loss", "label": "Unexplained Weight Loss", "category": "Metabolic / General"},
]


# --- clean_text ---
# What it does: Lowercases text, replaces non-alphanumeric punctuation with spaces, and condenses whitespace.
# Why it's structured this way: Prepares clinical complaints for lexical regex synonym matching.
# Parameters & Returns: text (str) -> cleaned string.
# ------------------------------------------------------------------------------
def clean_text(text: str) -> str:
    """Normalizes case, whitespace, and strips punctuation."""
    lowered = text.lower()
    cleaned = re.sub(r"[^\w\s-]", " ", lowered)
    return " ".join(cleaned.split())


# --- parse_symptoms ---
# What it does: Maps noisy free text or lists of symptom strings into a canonical multi-hot feature vector.
# Why it's structured this way: Prioritizes longer phrases first to prevent greedy matching and records unmapped tokens for clinical auditing.
# Parameters & Returns: input_data (Union[str, List[str]]) -> Dict containing canonical_symptoms, feature_vector, unmapped_tokens.
# ------------------------------------------------------------------------------
def parse_symptoms(input_data: Union[str, List[str]]) -> Dict[str, Any]:
    """
    Parses noisy free text or list of symptom strings into a canonical feature vector.
    Returns canonical symptoms, multi-hot feature vector, and unmatched tokens.
    """
    if isinstance(input_data, str):
        raw_items = [input_data]
        # Also split common delimiters (commas, 'and', semicolons, periods)
        sub_items = re.split(r"[,;.\n]|\band\b", input_data)
        raw_items.extend([s.strip() for s in sub_items if s.strip()])
    elif isinstance(input_data, (list, tuple)):
        raw_items = list(input_data)
    else:
        raw_items = [str(input_data)]

    detected_canonical = set()
    unmapped = []

    # Sort synonyms by length descending so longer phrases match first
    sorted_synonyms = sorted(SYMPTOM_SYNONYMS.items(), key=lambda x: len(x[0]), reverse=True)

    for item in raw_items:
        cleaned = clean_text(item)
        if not cleaned:
            continue

        matched_any = False
        # 1. Exact or substring match in cleaned item
        for phrase, canonical in sorted_synonyms:
            # Match whole words or boundary phrases
            pattern = r"(?:^|\b)" + re.escape(phrase) + r"(?:\b|$)"
            if re.search(pattern, cleaned):
                detected_canonical.add(canonical)
                matched_any = True

        if not matched_any and len(cleaned.split()) <= 4:
            # Check if this short token was unmatched
            if cleaned not in unmapped:
                unmapped.append(cleaned)

    # Cross-activation for synonyms & schema columns
    if "myalgia" in detected_canonical or "muscle_pain" in detected_canonical or "body_aches" in detected_canonical:
        detected_canonical.add("myalgia")
        detected_canonical.add("body_aches")
        detected_canonical.add("muscle_pain")

    if "sweating" in detected_canonical or "excessive_sweating" in detected_canonical:
        detected_canonical.add("sweating")
        detected_canonical.add("excessive_sweating")

    if "chills" in detected_canonical or "shivering" in detected_canonical or "rigors" in detected_canonical:
        detected_canonical.add("chills")
        detected_canonical.add("shivering")
        detected_canonical.add("rigors")

    if "fever" in detected_canonical or "high_fever" in detected_canonical:
        detected_canonical.add("fever")
        detected_canonical.add("high_fever")

    # Dermatology: scaly_rash <-> skin_peeling <-> itching <-> skin_rash <-> erythema
    if "scaly_rash" in detected_canonical:
        detected_canonical.add("scaly_rash")
        detected_canonical.add("skin_peeling")
        detected_canonical.add("itching")
        detected_canonical.add("skin_rash")
        detected_canonical.add("erythema")
    if "skin_peeling" in detected_canonical and ("skin_rash" in detected_canonical or "erythema" in detected_canonical):
        detected_canonical.add("scaly_rash")
        detected_canonical.add("itching")

    # Neurological: facial_droop <-> facial_palsy <-> cranial_nerve_deficit
    if ("facial_droop" in detected_canonical or "facial_palsy" in detected_canonical or "cranial_nerve_deficit" in detected_canonical):
        detected_canonical.add("facial_droop")
        detected_canonical.add("facial_palsy")
        detected_canonical.add("cranial_nerve_deficit")

    # Musculoskeletal: podagra <-> joint_pain <-> joint_swelling <-> erythema
    if "podagra" in detected_canonical:
        detected_canonical.add("podagra")
        detected_canonical.add("joint_pain")
        detected_canonical.add("joint_swelling")
        detected_canonical.add("erythema")

    # Abdominal: appendicitis hallmarks <-> abdominal_pain <-> rebound_tenderness
    if any(s in detected_canonical for s in ["acute_appendicitis", "rebound_tenderness", "right_lower_quadrant_pain", "periumbilical_pain"]):
        detected_canonical.add("abdominal_pain")
        detected_canonical.add("acute_appendicitis")
        detected_canonical.add("rebound_tenderness")
        detected_canonical.add("right_lower_quadrant_pain")

    canonical_list = [c for c in CANONICAL_SYMPTOMS if c in detected_canonical]
    feature_vector = {c: (1 if c in detected_canonical else 0) for c in CANONICAL_SYMPTOMS}

    return {
        "canonical_symptoms": canonical_list,
        "feature_vector": feature_vector,
        "unmapped_tokens": unmapped,
        "total_symptoms_detected": len(canonical_list),
    }


# --- get_canonical_symptom_catalog ---
# What it does: Returns static list of all registered clinical symptoms with human-readable labels and organ categories.
# Why it's structured this way: Fuels UI dropdown menus and search autocomplete in the patient portal.
# Parameters & Returns: None -> List of symptom metadata dictionaries.
# ------------------------------------------------------------------------------
def get_canonical_symptom_catalog() -> List[Dict[str, str]]:
    """Returns catalog of all registered canonical symptoms."""
    return CATALOG_METADATA


# --- suggest_related_symptoms ---
# What it does: Evaluates co-occurrence rules to recommend complementary symptoms to inquire about.
# Why it's structured this way: Guides the intake flow to collect discriminatory clinical signals (e.g. asking about chills if fever is reported).
# Parameters & Returns: canonical_symptoms (List[str]) -> List of suggested symptom strings.
# ------------------------------------------------------------------------------
def suggest_related_symptoms(canonical_symptoms: List[str]) -> List[str]:
    """Suggests relevant symptoms to ask the patient about based on input symptoms."""
    symptom_set = set(canonical_symptoms)
    suggestions = []

    if "cough" in symptom_set and "dyspnea" not in symptom_set:
        suggestions.append("dyspnea")
    if "fever" in symptom_set and "chills" not in symptom_set:
        suggestions.append("chills")
    if "fever" in symptom_set and "body_aches" not in symptom_set:
        suggestions.append("body_aches")
    if "polyuria" in symptom_set and "polydipsia" not in symptom_set:
        suggestions.append("polydipsia")
    if "headache" in symptom_set and "photophobia" not in symptom_set:
        suggestions.append("photophobia")
    if "nausea" in symptom_set and "diarrhea" not in symptom_set:
        suggestions.append("diarrhea")
    if "chest_pain" in symptom_set and "dyspnea" not in symptom_set:
        suggestions.append("dyspnea")

    return [s for s in suggestions if s in CANONICAL_SYMPTOMS and s not in symptom_set]
