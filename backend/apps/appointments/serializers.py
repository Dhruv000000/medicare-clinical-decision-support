# ==============================================================================
# FILE: backend/apps/appointments/serializers.py
# PURPOSE: DRF serializers for appointment creation, booking validation, and status updates.
# VIVA EXPLANATION: Validates doctor availability, ensures appointment times are strictly in the future, and decorates serialized output with patient and physician display names.
# ==============================================================================

from django.utils import timezone
from rest_framework import serializers
from apps.accounts.models import User
from .models import Appointment


# --- AppointmentSerializer ---
# What it does: Serializes Appointment instances for patient and doctor dashboards with display names and emails.
# Why it's structured this way: Provides a unified representation for calendar displays across both patient and doctor interfaces.
# Parameters & Returns: Returns complete serialized Appointment dictionary.
# ------------------------------------------------------------------------------
class AppointmentSerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(source="patient.email", read_only=True)
    patient_name = serializers.SerializerMethodField()
    doctor_email = serializers.EmailField(source="doctor.email", read_only=True)
    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "patient_email",
            "patient_name",
            "doctor",
            "doctor_email",
            "doctor_name",
            "starts_at",
            "reason",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "patient", "created_at", "updated_at"]

    def get_patient_name(self, obj):
        name = f"{obj.patient.first_name} {obj.patient.last_name}".strip()
        return name if name else obj.patient.email

    def get_doctor_name(self, obj):
        name = f"Dr. {obj.doctor.first_name} {obj.doctor.last_name}".strip()
        return name if name != "Dr." else f"Dr. {obj.doctor.email}"


# --- AppointmentCreateSerializer ---
# What it does: Validates patient booking requests, ensuring the target doctor exists and appointment is scheduled in the future.
# Why it's structured this way: Enforces temporal scheduling sanity (starts_at >= timezone.now()) and doctor existence.
# Parameters & Returns: Validates doctor_id, starts_at, reason, notes.
# ------------------------------------------------------------------------------
class AppointmentCreateSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Appointment
        fields = ["doctor_id", "starts_at", "reason", "notes"]

    def validate_doctor_id(self, value):
        try:
            doctor = User.objects.get(id=value, role=User.Roles.DOCTOR, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("A valid active doctor with this ID was not found.")
        return value

    def validate_starts_at(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Appointment time cannot be scheduled in the past.")
        return value


# --- AppointmentUpdateSerializer ---
# What it does: Serializes partial modifications to appointment status, time, or clinical notes.
# Why it's structured this way: Allows doctors to transition status (e.g. Scheduled -> Confirmed -> Completed).
# Parameters & Returns: Validates status, starts_at, reason, and notes.
# ------------------------------------------------------------------------------
class AppointmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["status", "starts_at", "reason", "notes"]
