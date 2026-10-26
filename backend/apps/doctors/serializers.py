# ==============================================================================
# FILE: backend/apps/doctors/serializers.py
# PURPOSE: Serializers for clinician profiles, clinical consultation notes, and patient summaries.
# VIVA EXPLANATION: Transforms DoctorProfile and ClinicalNote ORM models into JSON representations. Implements cross-domain authorization validation within ClinicalNoteSerializer.validate() to prevent doctors from filing notes on unauthorized patients.
# ==============================================================================

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from apps.accounts.models import User
from .models import DoctorProfile, ClinicalNote


# --- DoctorProfileSerializer ---
# What it does: Serializes clinician metadata including medical license, hospital affiliation, and specialty.
# Why it's structured this way: Pulls account fields (email, names) directly from related user model via source attributes.
# Parameters & Returns: DoctorProfile instance -> Serialized dictionary with read-only audit and verification stamps.
# ------------------------------------------------------------------------------
class DoctorProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = DoctorProfile
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "license_number",
            "specialization",
            "hospital",
            "experience_years",
            "bio",
            "is_verified",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_verified", "created_at", "updated_at"]


# --- ClinicalNoteSerializer ---
# What it does: Serializes physician SOAP clinical notes and verifies clinical access boundaries during validation.
# Why it's structured this way: Enforces doctor_can_access_patient within DRF validation pipeline to guarantee data integrity.
# Parameters & Returns: ClinicalNote instance <-> Serialized JSON with doctor_name and patient_email.
# ------------------------------------------------------------------------------
class ClinicalNoteSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    patient_email = serializers.EmailField(source="patient.email", read_only=True)

    class Meta:
        model = ClinicalNote
        fields = [
            "id",
            "doctor",
            "doctor_name",
            "patient",
            "patient_email",
            "diagnosis",
            "note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "doctor", "patient", "doctor_name", "patient_email", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        patient = self.context.get("patient") or attrs.get("patient")
        if request and request.user and getattr(request.user, "role", None) == "doctor" and patient:
            from core.permissions import doctor_can_access_patient
            if not doctor_can_access_patient(request.user, patient):
                raise PermissionDenied("Doctor does not have active clinical authorization for this patient.")
        return attrs

    def get_doctor_name(self, obj):
        name = f"{obj.doctor.first_name} {obj.doctor.last_name}".strip()
        return name if name else obj.doctor.email


# --- DoctorPatientSummarySerializer ---
# What it does: Serializes a patient user entity along with nested clinical profile details for doctor overview.
# Why it's structured this way: Employs SerializerMethodField for lazy loading to prevent circular serializer imports.
# Parameters & Returns: User instance -> Serialized patient representation including profile attributes.
# ------------------------------------------------------------------------------
class DoctorPatientSummarySerializer(serializers.ModelSerializer):
    patient_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "patient_profile"]

    def get_patient_profile(self, obj):
        if hasattr(obj, "patient_profile"):
            from apps.patients.serializers import PatientProfileSerializer
            return PatientProfileSerializer(obj.patient_profile).data
        return None

