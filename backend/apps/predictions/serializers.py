# ==============================================================================
# FILE: backend/apps/predictions/serializers.py
# PURPOSE: DRF serializers formatting disease predictions, TreeSHAP explainability vectors, and symptom NLP logs.
# VIVA EXPLANATION: Translates complex Django model instances containing JSONField structures (TreeSHAP attributions, feature matrices, vitals snapshots) into validated JSON schemas. Fields are marked read_only for audit integrity to prevent tampering.
# ==============================================================================

from rest_framework import serializers
from .models import DiseasePrediction, SymptomAnalysis


# --- DiseasePredictionSerializer ---
# What it does: Serializes historical DiseasePrediction model instances with TreeSHAP explanations.
# Why it's structured this way: Enforces read-only fields on historical clinical predictions to maintain regulatory audit integrity.
# Parameters & Returns: DiseasePrediction model instance -> Serialized prediction dictionary.
# ------------------------------------------------------------------------------
class DiseasePredictionSerializer(serializers.ModelSerializer):
    """
    Serializes historical DiseasePrediction model instances for clinicians and patients.

    Includes patient email, model metadata (XGBoost version), prediction results,
    and structured TreeSHAP feature attribution explanations.
    """
    patient_email = serializers.EmailField(
        source="patient.email",
        read_only=True,
        help_text="Email address of the evaluated patient.",
    )

    class Meta:
        model = DiseasePrediction
        fields = [
            "id",
            "patient",
            "patient_email",
            "model_name",
            "model_version",
            "input_data",
            "predicted_condition",
            "confidence",
            "explanation",
            "created_at",
        ]
        read_only_fields = fields


# --- SymptomAnalysisSerializer ---
# What it does: Serializes historical SymptomAnalysis sessions for clinical review.
# Why it's structured this way: Exposes extracted canonical symptoms and co-occurring suggestions for patient history views.
# Parameters & Returns: SymptomAnalysis model instance -> Serialized dictionary.
# ------------------------------------------------------------------------------
class SymptomAnalysisSerializer(serializers.ModelSerializer):
    """
    Serializes historical SymptomAnalysis sessions for clinical review.
    """
    patient_email = serializers.EmailField(
        source="patient.email",
        read_only=True,
        help_text="Email address of the evaluated patient.",
    )

    class Meta:
        model = SymptomAnalysis
        fields = [
            "id",
            "patient",
            "patient_email",
            "symptoms_text",
            "result",
            "created_at",
        ]
        read_only_fields = fields
