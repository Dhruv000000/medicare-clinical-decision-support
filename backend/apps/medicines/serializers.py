# ==============================================================================
# FILE: backend/apps/medicines/serializers.py
# PURPOSE: Serializer for Medication records with clinical authorization validation.
# VIVA EXPLANATION: Validates incoming prescription payloads and serializes medication details including prescribing physician names and active statuses.
# ==============================================================================

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from .models import Medication


# --- MedicationSerializer ---
# What it does: Serializes Medication objects and enforces doctor_can_access_patient authorization during creation.
# Why it's structured this way: Read-only patient and timestamps prevent tampering; dynamic SerializerMethodField provides doctor name.
# Parameters & Returns: ModelSerializer subclass.
# ------------------------------------------------------------------------------
class MedicationSerializer(serializers.ModelSerializer):
    prescribed_by_name = serializers.SerializerMethodField()
    patient_email = serializers.EmailField(source="patient.email", read_only=True)

    class Meta:
        model = Medication
        fields = [
            "id",
            "patient",
            "patient_email",
            "name",
            "dosage",
            "frequency",
            "prescribed_by",
            "prescribed_by_name",
            "start_date",
            "end_date",
            "is_active",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "patient", "created_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        target_patient = self.context.get("target_patient")
        if request and request.user and getattr(request.user, "role", None) == "doctor" and target_patient:
            from core.permissions import doctor_can_access_patient
            if not doctor_can_access_patient(request.user, target_patient):
                raise PermissionDenied("Doctor does not have active clinical authorization for this patient.")
        return attrs

    def get_prescribed_by_name(self, obj):
        if obj.prescribed_by:
            name = f"Dr. {obj.prescribed_by.first_name} {obj.prescribed_by.last_name}".strip()
            return name if name != "Dr." else f"Dr. {obj.prescribed_by.email}"
        return None
