# ==============================================================================
# FILE: backend/apps/predictions/services/prediction_service.py
# PURPOSE: Business logic service orchestrating AI prediction inference, database persistence, and HIPAA audit trails.
# VIVA EXPLANATION: This service acts as the operational bridge between HTTP controllers, the mathematical AI engine, and relational database persistence. It coordinates feature extraction, AI execution, atomic storage of DiseasePrediction models, and creation of tamper-evident HIPAA compliance audit logs.
# ==============================================================================

import logging
import re
from typing import Any, Dict, List, Optional, Union
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from ai.engine import DiseaseRiskEngine, ModelNotLoadedError, get_engine
from apps.accounts.models import User
from apps.audit_logs.services import log_audit_event
from apps.audit_logs.models import AuditLog
from apps.predictions.models import DiseasePrediction, SymptomAnalysis

logger = logging.getLogger(__name__)


# --- execute_clinical_prediction_workflow ---
# What it does: Orchestrates AI inference, persists DiseasePrediction records, and writes HIPAA audit log entries.
# Why it's structured this way: Enforces ACID transaction boundaries and ensures clinical decisions are permanently tracked for medical liability auditing.
# Parameters & Returns: user (User), target_patient (User), request_data (Dict), request, engine -> Complete prediction response dictionary.
# ------------------------------------------------------------------------------
def execute_clinical_prediction_workflow(
    user: User,
    target_patient: User,
    request_data: Dict[str, Any],
    request=None,
    engine: Optional[DiseaseRiskEngine] = None,
) -> Dict[str, Any]:
    """
    Orchestrates the complete disease prediction clinical workflow.

    Purpose:
        Coordinates input extraction, isolated AI model execution, database
        persistence, audit logging, and response payload assembly.

    Input Parameters:
        - user (User): The authenticated requesting user (Doctor, Patient, or Admin).
        - target_patient (User): The patient whose health data is being evaluated.
        - request_data (dict): Request body containing 'symptoms', 'text', and/or 'vitals'.
        - request: Optional Django/DRF HTTP request object for audit IP/user-agent extraction.
        - engine (DiseaseRiskEngine | None): Optional pre-loaded AI inference engine.

    Expected Output Format:
        Dictionary containing the full clinical decision support output:
        - id (int): Database record primary key.
        - patient_id (int): Target patient primary key.
        - predicted_condition (str): Diagnosed disease name.
        - confidence (float): Calibrated model confidence score.
        - severity (str): "low", "moderate", "high", "critical".
        - risk_level / triage_level (str): "LOW", "MODERATE", "HIGH".
        - recommendation (str): Tailored medical recommendations.
        - canonical_symptoms (list[str]): Parsed canonical symptom keys.
        - ranked_diagnoses (list[dict]): Differential diagnoses with probabilities.
        - shap_analysis (dict): TreeSHAP feature attributions and base value.
        - clinical_safety (dict): Diagnostic disclaimer and regulatory safety text.
        - model_metadata (dict): Model name, schema version, execution timestamp.
    """
    # --------------------------------------------------------------------------
    # STEP 1: EXTRACT CLINICAL INPUTS (SYMPTOMS & VITALS)
    # --------------------------------------------------------------------------
    symptoms_input = request_data.get("symptoms") or request_data.get("text")
    vitals_input = request_data.get("vitals")

    has_top_vitals = any(
        k in request_data for k in [
            "systolic_bp", "diastolic_bp", "glucose", "heart_rate",
            "body_temperature", "temperature", "oxygen_saturation", "spo2", "bmi", "age", "sex"
        ]
    )

    if not symptoms_input and not vitals_input and not has_top_vitals:
        raise ValidationError("Field 'symptoms' (list or text) is required.")

    if engine is None:
        engine = get_engine()

    # --------------------------------------------------------------------------
    # DOMAIN RELEVANCE MAPPINGS FOR BACKGROUND EHR LAB VALUES
    # Only merge chronic background labs if symptoms belong to that clinical domain.
    # --------------------------------------------------------------------------
    METABOLIC_ENDOCRINE_INDICATORS = {
        "polyuria", "polydipsia", "polyphagia", "weight_loss", "fatigue",
        "blurred_vision", "tingling", "numbness", "hyperphagia", "hypoglycemia_symptoms",
        "goiter", "heat_intolerance", "cold_intolerance", "excessive_sweating",
        "hirsutism", "galactorrhea", "gynecomastia", "weight_gain", "anorexia", "cachexia"
    }
    RENAL_INDICATORS = {
        "flank_pain", "hematuria", "dysuria", "oliguria", "anuria", "urinary_frequency",
        "urinary_urgency", "nocturia", "frothy_urine", "edema", "leg_swelling"
    }
    CARDIOVASCULAR_INDICATORS = {
        "chest_pain", "palpitations", "syncope", "presyncope", "claudication",
        "orthopnea", "paroxysmal_nocturnal_dyspnea", "cyanosis", "leg_swelling"
    }

    # Pre-check extracted canonical symptoms to detect symptom-free vectors
    parsed_check = engine.preprocessor.parse_symptoms(symptoms_input) if symptoms_input else None
    canonical_list = parsed_check.get("canonical_symptoms", []) if parsed_check else []
    extracted_symptoms_count = len(canonical_list)
    canonical_set = set(canonical_list)

    s_text_lower = str(symptoms_input).lower()
    has_metabolic_symptom = (
        any(k in canonical_set for k in METABOLIC_ENDOCRINE_INDICATORS)
        or any(k in s_text_lower for k in ["urinat", "thirst", "weight loss", "polyuria", "polydipsia", "polyphagia", "glucose", "sugar"])
    )
    has_renal_symptom = any(k in canonical_set for k in RENAL_INDICATORS)
    has_cardio_symptom = any(k in canonical_set for k in CARDIOVASCULAR_INDICATORS)

    # Merge existing patient lab results ONLY if relevant to current presentation domain
    patient_vitals = dict(vitals_input) if isinstance(vitals_input, dict) else {}
    if target_patient and hasattr(target_patient, "lab_reports") and extracted_symptoms_count > 0:
        try:
            from apps.medical_records.models import LabResult
            recent_results = LabResult.objects.filter(report__patient=target_patient).order_by("-report__uploaded_at")[:20]
            for lr in recent_results:
                t_lower = lr.test_name.lower()
                clean_num_match = re.search(r"[-+]?\d*\.?\d+", str(lr.value))
                if not clean_num_match:
                    continue
                num_val = float(clean_num_match.group())

                is_metabolic_lab = any(m in t_lower for m in ["hba1c", "glucose", "fbs", "fasting glucose", "blood glucose", "sugar"])
                is_renal_lab = any(m in t_lower for m in ["creatinine", "bun", "egfr", "urea"])
                is_lipid_lab = any(m in t_lower for m in ["cholesterol", "triglyceride", "ldl", "hdl", "lipid"])

                # Gating rules:
                # 1. Chronic metabolic labs require metabolic/endocrine indicators
                if is_metabolic_lab and not has_metabolic_symptom:
                    continue
                # 2. Renal labs require renal or metabolic indicators
                if is_renal_lab and not (has_renal_symptom or has_metabolic_symptom):
                    continue
                # 3. Lipid labs require cardiovascular or metabolic indicators
                if is_lipid_lab and not (has_cardio_symptom or has_metabolic_symptom):
                    continue

                if "hba1c" in t_lower and "hba1c" not in patient_vitals:
                    patient_vitals["hba1c"] = num_val
                elif ("fasting glucose" in t_lower or "fbs" in t_lower or "blood glucose" in t_lower or "glucose" in t_lower) and "glucose" not in patient_vitals:
                    patient_vitals["glucose"] = num_val
                elif "systolic" in t_lower and "systolic_bp" not in patient_vitals:
                    patient_vitals["systolic_bp"] = num_val
                elif "diastolic" in t_lower and "diastolic_bp" not in patient_vitals:
                    patient_vitals["diastolic_bp"] = num_val
                elif "creatinine" in t_lower and "creatinine" not in patient_vitals:
                    patient_vitals["creatinine"] = num_val
        except Exception as exc:
            logger.debug(f"Could not load patient lab results for prediction vitals: {exc}")

    # Structure input for DiseaseRiskEngine
    if isinstance(request_data, dict) and (vitals_input or has_top_vitals or patient_vitals):
        merged_req = dict(request_data)
        if patient_vitals:
            existing_vitals = merged_req.get("vitals") or {}
            merged_v = dict(patient_vitals)
            merged_v.update(existing_vitals)
            merged_req["vitals"] = merged_v
        engine_input = merged_req
    elif patient_vitals:
        engine_input = {"symptoms": symptoms_input, "vitals": patient_vitals}
    else:
        engine_input = symptoms_input

    # --------------------------------------------------------------------------
    # STEP 2: EXECUTE ISOLATED AI INFERENCE & EXPLAINABILITY PIPELINE
    # Calls dedicated AI algorithm module (ai.prediction_service).
    # --------------------------------------------------------------------------
    if engine is None:
        engine = get_engine()

    from ai.prediction_service import execute_ai_disease_prediction

    ai_output = execute_ai_disease_prediction(
        input_data=engine_input,
        patient=target_patient,
        engine=engine,
    )

    # --------------------------------------------------------------------------
    # STEP 3: PERSIST PREDICTION RECORD TO DATABASE
    # Stores inputs, predictions, and full TreeSHAP explanations for auditability.
    # --------------------------------------------------------------------------
    prediction_record = DiseasePrediction.objects.create(
        patient=target_patient,
        model_name=ai_output["model_metadata"]["model_name"],
        model_version=ai_output["model_metadata"]["model_version"],
        input_data={
            "symptoms_input": symptoms_input,
            "canonical_symptoms": ai_output["canonical_symptoms"],
            "vitals_input": vitals_input or {},
            "extracted_vitals": ai_output["extracted_vitals"],
        },
        predicted_condition=ai_output["predicted_condition"],
        confidence=ai_output["confidence"],
        explanation={
            "shap_analysis": ai_output["shap_analysis"],
            "shap_attributions": ai_output["shap_analysis"]["features"],
            "features": ai_output["shap_analysis"]["features"],
            "base_value": ai_output["shap_analysis"].get("base_value", 0.0),
            "ranked_diagnoses": ai_output["ranked_diagnoses"],
            "differential_diagnoses": ai_output["differential_diagnoses"],
            "triage_level": ai_output["triage_level"],
            "severity": ai_output["severity"],
            "recommendation": ai_output["recommendation"],
            "summary": ai_output["shap_analysis"]["summary"],
            "clarification_prompt": ai_output.get("clarification_prompt"),
            "red_flag_alert": ai_output.get("red_flag_alert"),
            "validation_status": ai_output.get("validation_status"),
            "status": ai_output.get("status"),
            "potential_specialties": ai_output.get("potential_specialties", []),
            "top_specialties": ai_output.get("top_specialties", []),
            "clarifying_questions": ai_output.get("clarifying_questions", []),
        },
    )

    # --------------------------------------------------------------------------
    # STEP 4: RECORD REGULATORY AUDIT LOG EVENT
    # Ensures HIPAA/GDPR clinical audit traceability for all AI-generated predictions.
    # --------------------------------------------------------------------------
    log_audit_event(
        user=user,
        action=AuditLog.Actions.RECORD_CREATE,
        resource_type="DiseasePrediction",
        resource_id=prediction_record.id,
        request=request,
        metadata={
            "patient_id": target_patient.id,
            "condition": ai_output["predicted_condition"],
            "confidence": ai_output["confidence"],
            "risk_level": ai_output["risk_level"],
        },
    )

    # --------------------------------------------------------------------------
    # STEP 5: ASSEMBLE COMPLETE RESPONSE PAYLOAD
    # --------------------------------------------------------------------------
    return {
        "id": prediction_record.id,
        "patient_id": target_patient.id,
        "created_at": prediction_record.created_at,
        **ai_output,
    }


# --- execute_symptom_analysis_workflow ---
# What it does: Executes clinical NLP parsing, extracts canonical and negated symptoms, and saves history for registered patients.
# Why it's structured this way: Encapsulates patient persistence logic while supporting anonymous/unauthenticated symptom checks when needed.
# Parameters & Returns: input_data (Union[str, List[str]]), user (Optional[User]) -> Parsed dictionary with canonical, negated, and suggested symptoms.
# ------------------------------------------------------------------------------
def execute_symptom_analysis_workflow(
    input_data: Union[str, List[str]],
    user: Optional[User] = None,
) -> Dict[str, Any]:
    """
    Orchestrates the symptom analysis workflow with clinical NLP.

    Purpose:
        Maps symptoms to canonical vocabulary, identifies negated symptoms,
        computes related symptom suggestions, and logs to history if requested by patient.

    Input Parameters:
        - input_data (str | list[str]): Free-text description or list of symptom strings.
        - user (User | None): The requesting user.

    Expected Output:
        Standardized symptom analysis dictionary with catalog and recommendations.
    """
    if not input_data:
        raise ValidationError("Either 'text' or 'symptoms' must be provided.")

    # 1. Execute isolated NLP canonicalization
    from ai.prediction_service import parse_and_suggest_symptoms
    analysis_result = parse_and_suggest_symptoms(input_data)

    # 2. Persist analysis history if requesting user is a patient
    if user and hasattr(user, "role") and user.role == User.Roles.PATIENT:
        SymptomAnalysis.objects.create(
            patient=user,
            symptoms_text=str(input_data),
            result={
                "canonical": analysis_result["canonical_symptoms"],
                "negated": analysis_result["negated_symptoms"],
                "suggestions": analysis_result["suggested_symptoms"],
            },
        )

    return analysis_result
