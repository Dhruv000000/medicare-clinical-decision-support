# ==============================================================================
# FILE: backend/apps/medical_records/serializers.py
# PURPOSE: DRF serializers for medical records, diagnostic lab reports, and extracted quantitative biomarkers.
# VIVA EXPLANATION: Translates complex clinical records and parsed lab tests (with abnormal flags and reference ranges) into validated JSON schemas while enforcing doctor-patient relationship authorization boundaries.
# ==============================================================================


from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from .models import MedicalRecord, LabReport, LabResult


# --- LabResultSerializer ---
# What it does: Serializes discrete laboratory biomarker results with reference ranges and abnormal flags.
# Why it's structured this way: Encapsulates quantitative biomarker metrics for structured lab rendering.
# Parameters & Returns: LabResult model instance -> Serialized dictionary.
# ------------------------------------------------------------------------------
class LabResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabResult
        fields = ["id", "test_name", "value", "unit", "reference_range", "flag"]


# --- LabReportSerializer ---
# What it does: Serializes uploaded lab reports along with nested structured LabResult biomarkers.
# Why it's structured this way: Generates fully-qualified secure media URLs and exposes OCR extracted summaries.
# Parameters & Returns: LabReport model instance -> Serialized dictionary with nested results.
# ------------------------------------------------------------------------------
class LabReportSerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(
        source="patient.email",
        read_only=True,
        help_text="Email of the patient receiving the lab diagnostic.",
    )
    results = LabResultSerializer(
        many=True,
        read_only=True,
        help_text="Extracted quantitative biomarker items.",
    )
    file_url = serializers.SerializerMethodField(
        help_text="Fully-qualified URL to access the report file.",
    )

    class Meta:
        model = LabReport
        fields = [
            "id",
            "patient",
            "patient_email",
            "title",
            "file",
            "file_url",
            "file_type",
            "file_size",
            "extracted_text",
            "analysis_summary",
            "results",
            "uploaded_at",
        ]
        read_only_fields = [
            "id",
            "patient",
            "file_size",
            "file_type",
            "extracted_text",
            "analysis_summary",
            "results",
            "uploaded_at",
        ]

    def get_file_url(self, obj):
        """Constructs absolute URL for accessing the laboratory file."""
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


# --- MedicalRecordSerializer ---
# What it does: Serializes clinical encounters, history notes, and diagnoses while enforcing access boundaries.
# Why it's structured this way: Validates doctor authorization boundary via doctor_can_access_patient before saving.
# Parameters & Returns: MedicalRecord model instance -> Serialized dictionary.
# ------------------------------------------------------------------------------
class MedicalRecordSerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(
        source="patient.email",
        read_only=True,
        help_text="Email of the patient.",
    )

    class Meta:
        model = MedicalRecord
        fields = [
            "id",
            "patient",
            "patient_email",
            "title",
            "record_type",
            "description",
            "recorded_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "patient", "created_at", "updated_at"]

    def validate(self, attrs):
        """Validates doctor authorization boundary before record creation."""
        request = self.context.get("request")
        target_patient = self.context.get("target_patient")
        if request and request.user and getattr(request.user, "role", None) == "doctor" and target_patient:
            from core.permissions import doctor_can_access_patient
            if not doctor_can_access_patient(request.user, target_patient):
                raise PermissionDenied("Doctor does not have active clinical authorization for this patient.")
        return attrs
