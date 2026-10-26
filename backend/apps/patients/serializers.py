# ==============================================================================
# FILE: backend/apps/patients/serializers.py
# PURPOSE: Serializer and validation logic for patient demographic and clinical profiles.
# VIVA EXPLANATION: Validates patient profile updates including blood group normalization against medical standards (A+, O-, etc.), date-of-birth temporal sanity checks, and propagates name updates to the parent User model.
# ==============================================================================

from django.utils import timezone
from rest_framework import serializers
from .models import PatientProfile


# --- PatientProfileSerializer ---
# What it does: Serializes PatientProfile models to JSON and validates medical fields like blood group and DOB.
# Why it's structured this way: Implements custom update() logic to synchronize user names (first_name, last_name) across models.
# Parameters & Returns: PatientProfile instance <-> Serialized JSON representation.
# ------------------------------------------------------------------------------
class PatientProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", required=False)
    last_name = serializers.CharField(source="user.last_name", required=False)

    VALID_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", ""}

    class Meta:
        model = PatientProfile
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "blood_group",
            "phone",
            "address",
            "emergency_contact",
            "medical_history_summary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_blood_group(self, value):
        if value:
            normalized = value.strip().upper()
            if normalized not in self.VALID_BLOOD_GROUPS:
                raise serializers.ValidationError(
                    f"Invalid blood group '{value}'. Valid options are: A+, A-, B+, B-, AB+, AB-, O+."
                )
            return normalized
        return ""

    def validate_date_of_birth(self, value):
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        user = instance.user
        user_updated = False
        if "first_name" in user_data:
            user.first_name = user_data["first_name"]
            user_updated = True
        if "last_name" in user_data:
            user.last_name = user_data["last_name"]
            user_updated = True
        if user_updated:
            user.save(update_fields=["first_name", "last_name", "updated_at"])

        return super().update(instance, validated_data)


