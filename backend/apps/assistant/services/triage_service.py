# ==============================================================================
# FILE: backend/apps/assistant/services/triage_service.py
# PURPOSE: High-acuity red-flag emergency triage service with negation detection
#          and GI reflux / acute cardiac distress differentiation.
# VIVA EXPLANATION: Implements the Rule-based Triage and Chain-of-Responsibility
# pattern. Filters life-threatening emergencies (stroke, cardiac crisis, severe
# respiratory failure, hemorrhage, loss of consciousness, anaphylaxis) while
# performing negation-window checking and preventing false positives on mild
# gastroesophageal reflux / heartburn complaints.
# ==============================================================================

import re
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

NEGATION_TOKENS = {
    "no", "not", "denies", "denied", "without", "never",
    "neither", "nor", "rules", "ruled", "negative", "none",
    "zero", "unremarkable", "didnt", "doesnt", "cannot", "cant",
}

MULTI_WORD_NEGATIONS = [
    "negative for",
    "rules out",
    "ruled out",
    "free of",
    "no signs of",
    "no sign of",
    "not experiencing",
    "without any",
    "denies any",
    "did not",
    "does not",
]

GI_REFLUX_MARKERS = [
    "after eating",
    "after meals",
    "after meal",
    "after food",
    "after dinner",
    "after lunch",
    "spicy meals",
    "spicy meal",
    "spicy food",
    "spicy foods",
    "lying down",
    "lies down",
    "lay down",
    "laid down",
    "heartburn",
    "acid reflux",
    "sour taste",
    "bitter taste",
    "antacids",
    "antacid",
    "mild burning",
    "burning sensation in my chest",
    "burning in my chest",
    "burning sensation in chest",
    "burning in chest",
    "indigestion",
    "gerd",
    "reflux",
    "regurgitation",
    "burping",
    "belching",
    "full stomach",
    "bloating",
]


def is_negated(text: str, match_start: int, window: int = 3) -> bool:
    """
    Checks whether a matched clinical symptom is preceded by a negation token
    within a specified word window (default 3 words) in the active clause.
    Prevents crossing clause delimiters (. ! ? ; : or contrastive conjunctions).
    """
    text_before = text[:match_start]
    # Split on sentence boundaries and contrastive conjunctions
    parts = re.split(
        r'([.!?;:\n]|\bbut\b|\bhowever\b|\balthough\b|\byet\b|\bexcept\b)',
        text_before,
        flags=re.IGNORECASE,
    )
    clause = parts[-1] if parts else ""
    clause_lower = clause.lower().strip()

    # 1. Check multi-word negation phrases
    for mwn in MULTI_WORD_NEGATIONS:
        if mwn in clause_lower:
            idx = clause_lower.rfind(mwn)
            between = clause_lower[idx + len(mwn):]
            between_words = re.findall(r"\b[a-zA-Z']+\b", between)
            if len(between_words) <= window:
                return True

    # 2. Check single-word negation tokens within window
    words = re.findall(r"\b[a-zA-Z']+\b", clause_lower)
    trailing_words = words[-window:] if len(words) >= window else words
    for tw in trailing_words:
        clean_tw = tw.replace("'", "")
        if clean_tw in NEGATION_TOKENS or tw in NEGATION_TOKENS:
            return True

    return False


def has_active_match(text: str, pattern: str, window: int = 3) -> bool:
    """
    Returns True if pattern matches text and at least one occurrence is non-negated.
    """
    for m in re.finditer(pattern, text, re.IGNORECASE):
        if not is_negated(text, m.start(), window=window):
            return True
    return False


def has_gi_reflux_markers(text: str) -> bool:
    """
    Returns True if gastrointestinal reflux or heartburn markers are present.
    """
    t = text.lower()
    return any(marker in t for marker in GI_REFLUX_MARKERS)


class EmergencyTriageService:
    """
    Emergency Triage filter evaluating red-flag clinical conditions:
    - Acute Stroke presentation
    - High-Acuity Cardiac Events (differentiated from reflux/GERD)
    - Severe Respiratory Failure
    - Massive Hemorrhage
    - Loss of Consciousness / Acute Confusion
    - Anaphylaxis
    """

    def detect_emergency(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Detects urgent red-flag clinical symptoms requiring immediate emergency triage.
        Catches acute cardiac distress, respiratory failure, stroke signs, severe hemorrhage,
        and loss of consciousness prior to triggering RAG retrieval or LLM inference.
        """
        if not prompt or not prompt.strip():
            return None

        p = prompt.strip()
        matched_categories = []

        # ----------------------------------------------------------------------
        # 1. STROKE SYMPTOMS (Negation-aware)
        # ----------------------------------------------------------------------
        stroke_pattern = (
            r"("
            r"\b(stroke|cva|cerebrovascular\s+accident|tia|transient\s+ischemic\s+attack)\b|"
            r"\b(facial\s+(droop(ing)?|weakness|paralysis|numbness)|face\s+(droop(ing)?|weakness|paralysis|numbness)|drooping\s+(face|mouth|eye|eyelid|smile))\b|"
            r"\b((left|right|one)\s+side\s+of\s+(my\s+)?face\b.*?\b(weak|droop|paralyz|numb|sag))\b|"
            r"\b(face\b.*?\b(weak|droop|paralyz|numb|sag))\b|"
            r"\b((left|right|one)[- ]sided?(\s+side)?\b.*?\b(weak|numb|paralyz|limp|loss\s+of\s+(movement|sensation)))\b|"
            r"\bweakness\s+(on|in)\s+(one\s+side|one\s+half|left\s+side|right\s+side)\b|"
            r"\b(sudden|acute|new)\s+(numbness|weakness|paralysis)\b|"
            r"\b(speech\b.*?\bslurr(ed|ing)?|\bslurr(ed|ing)?\b.*?\b(speech|words?)|slurring\s+(words|speech))\b|"
            r"\b(loss\s+of\s+speech|unable\s+to\s+speak|(can\'?t|cannot)\s+speak|difficulty\s+speaking|trouble\s+speaking|unable\s+to\s+talk)\b|"
            r"\b((can\'?t|cannot|unable\s+to|difficulty|trouble|hard\s+to)\s+(lift|raise|move|use)\s+(my\s+)?(left\s+|right\s+)?(arm|leg|hand|foot|limb))\b|"
            r"\b((left\s+|right\s+)?(arm|leg|hand|foot|limb)\b.*?\b(weak|limp|numb|paralyz|heavy|feels\s+weak|is\s+weak))\b|"
            r"\b(sudden\s+)?(arm|leg)\s+weakness\b"
            r")"
        )
        if has_active_match(p, stroke_pattern):
            matched_categories.append("stroke_symptoms")

        # ----------------------------------------------------------------------
        # 2. DEFINITE HIGH-ACUITY CARDIAC DRIVERS (Negation-aware)
        # ----------------------------------------------------------------------
        radiation_pattern = (
            r"("
            r"\b(radiat(ing|es|ed)|spread(ing|s))\s*(to\s*)?(the\s*|my\s*)?(left\s+|right\s+)?(arm|arms|shoulder|shoulders|jaw|neck|back)\b|"
            r"\b(left\s+)?arm\s+pain\b|"
            r"\bpain\s+(in|down)\s+(my\s+)?(left\s+)?arm\b|"
            r"\bpain\s+in\s+(my\s+)?(jaw|shoulder|neck|back)\b"
            r")"
        )
        active_radiation = has_active_match(p, radiation_pattern)

        dyspnea_cardiac_pattern = (
            r"("
            r"\b((acute|severe|sudden|extreme)\s+)?(shortness\s+of\s+breath|breathlessness|dyspnea)\b|"
            r"\b(can\'?t|cannot|unable\s+to)\s+breathe\b|"
            r"\bgasping\s+for\s+(air|breath)\b|"
            r"\b(choking|suffocating)\b|"
            r"\b(struggling\s+to\s+breathe|trouble\s+breathing|difficulty\s+breathing)\b"
            r")"
        )
        active_dyspnea = has_active_match(p, dyspnea_cardiac_pattern)

        sweating_cardiac_pattern = (
            r"("
            r"\b(cold\s+sweat(s|ing)?|profuse\s+sweat(ing)?|diaphoresis|drenched\s+in\s+sweat|breaking\s+out\s+in\s+(a\s+)?cold\s+sweat)\b|"
            r"\b(sweat(ing)?|diaphoretic)\b"
            r")"
        )
        active_sweating = has_active_match(p, sweating_cardiac_pattern)

        crushing_or_syncope_pattern = (
            r"("
            r"\b(crushing|squeezing|vice-like|strangling)\s+(chest\s+)?(pressure|pain|tightness|discomfort)?\b|"
            r"\belephant\s+(is\s+)?(sitting\s+)?(on|across)\s+(my\s+)?chest\b|"
            r"\b(syncope|fainted|loss\s+of\s+consciousness|blacked?\s+out|passed\s+out|unresponsive)\b|"
            r"\b(cardiac\s+arrest|heart\s+attack|myocardial\s+infarction)\b"
            r")"
        )
        active_crushing_or_syncope = has_active_match(p, crushing_or_syncope_pattern)

        acute_chest_pain_pattern = (
            r"("
            r"\b(acute|severe|sudden)\s+(left\s+)?(chest\s+pain|pain\s+in\s+(my\s+)?(heart|chest)|heart\s+pain|chest\s+pressure)\b|"
            r"\bpain\s+in\s+(my\s+)?heart\b|"
            r"\bheart\s+pain\b"
            r")"
        )
        active_acute_heart_pain = has_active_match(p, acute_chest_pain_pattern)

        general_chest_pattern = (
            r"("
            r"\bchest\s+(pain|pressure|tightness|heaviness|discomfort|hurts|ache|distress)\b|"
            r"\b(pressure|tightness|heaviness)\s+(on|in|across)\s+(my\s+)?(chest|heart)\b|"
            r"\bleft\s+chest\s+pain\b|"
            r"\bangina\b"
            r")"
        )
        active_chest_pain = has_active_match(p, general_chest_pattern)

        has_gi = has_gi_reflux_markers(p)
        has_cardiac_drivers = bool(
            active_radiation or active_dyspnea or active_sweating or active_crushing_or_syncope
        )

        # Cardiac Emergency Decision Logic:
        # If GI reflux markers are present (e.g. after eating spicy meals and lying down, heartburn, gerd):
        # Only fire emergency alert if accompanied by active ischemic red flags (radiation, crushing pressure, acute dyspnea, cold sweat)
        # If NO GI markers:
        # Trigger if active crushing/syncope, acute heart pain, or chest pain with active drivers (radiation, dyspnea, sweating)
        # Suppress emergency alert on bare word 'chest', mild burning, or negated symptoms
        if has_gi:
            if active_crushing_or_syncope or active_radiation or (active_chest_pain and (active_dyspnea or active_sweating)):
                matched_categories.append("chest_pain")
        else:
            if active_crushing_or_syncope:
                matched_categories.append("chest_pain")
            elif active_acute_heart_pain:
                matched_categories.append("chest_pain")
            elif active_chest_pain and has_cardiac_drivers:
                matched_categories.append("chest_pain")

        # ----------------------------------------------------------------------
        # 3. RESPIRATORY DISTRESS (Negation-aware standalone)
        # ----------------------------------------------------------------------
        standalone_respiratory_pattern = (
            r"("
            r"\b(acute|severe|sudden|extreme)\s+(shortness\s+of\s+breath|breathlessness|dyspnea)\b|"
            r"\b(can\'?t|cannot|unable\s+to)\s+breathe\b|"
            r"\bgasping\s+for\s+(air|breath)\b|"
            r"\b(choking|suffocating)\b"
            r")"
        )
        if has_active_match(p, standalone_respiratory_pattern) and "chest_pain" not in matched_categories:
            matched_categories.append("respiratory_distress")

        # ----------------------------------------------------------------------
        # 4. SEVERE HEMORRHAGE (Negation-aware)
        # ----------------------------------------------------------------------
        hemorrhage_pattern = (
            r"("
            r"\b(severe|massive|profuse|uncontrolled)\s+(bleeding|hemorrhage)\b|"
            r"\b(coughing|vomiting)\s+up\s+blood\b|"
            r"\bbleeding\s+uncontrollably\b|"
            r"\b(hemoptysis|hematemesis)\b"
            r")"
        )
        if has_active_match(p, hemorrhage_pattern):
            matched_categories.append("severe_hemorrhage")

        # ----------------------------------------------------------------------
        # 5. LOSS OF CONSCIOUSNESS / ACUTE CONFUSION (Negation-aware)
        # ----------------------------------------------------------------------
        loc_pattern = (
            r"("
            r"\b((sudden|acute)\s+)?loss\s+of\s+consciousness\b|"
            r"\b(lost\s+consciousness|passed\s+out|unconscious|fainted|fainting|blackout|blacked\s+out|unresponsive)\b|"
            r"\b(feel(s|ing)?\s+confused|feeling\s+disoriented|new\s+confusion|acute\s+confusion|severe\s+confusion|sudden\s+confusion|disoriented|disorientation|altered\s+mental\s+status)\b|"
            r"\b(new|acute|severe)\s+confusion\b|"
            r"\b(acute\s+)?altered\s+mental\s+status\b|"
            r"\bsevere\s+disorientation\b"
            r")"
        )
        if has_active_match(p, loc_pattern) and "chest_pain" not in matched_categories:
            matched_categories.append("loss_of_consciousness")

        # ----------------------------------------------------------------------
        # 6. ANAPHYLAXIS (Negation-aware)
        # ----------------------------------------------------------------------
        anaphylaxis_pattern = (
            r"("
            r"\b(anaphylaxis|anaphylactic(\s+shock)?)\b|"
            r"\bthroat\s+closing\b|"
            r"\bswelling\s+of\s+(the\s+)?(throat|tongue|lips|airway)\b|"
            r"\bsevere\s+allergic\s+reaction\b"
            r")"
        )
        if has_active_match(p, anaphylaxis_pattern):
            matched_categories.append("anaphylaxis")

        if matched_categories:
            return {
                "is_emergency": True,
                "categories": matched_categories,
            }
        return None


triage_service = EmergencyTriageService()
detect_emergency = triage_service.detect_emergency

__all__ = [
    "EmergencyTriageService",
    "triage_service",
    "detect_emergency",
    "is_negated",
    "has_active_match",
    "has_gi_reflux_markers",
    "GI_REFLUX_MARKERS",
    "NEGATION_TOKENS",
]
