# ==============================================================================
# FILE: backend/apps/patients/models.py
# PURPOSE: Data model for patient clinical demographic profiles, blood groups, and medical history.
# VIVA EXPLANATION: Defines PatientProfile linked via a OneToOneField to the central User authentication model. Stores vital clinical baseline demographics required for clinical decision support and personalized risk scoring.
# ==============================================================================

from django.conf import settings
from django.db import models


# --- PatientProfile ---
# What it does: Stores demographic data (DOB, blood group, emergency contact) and baseline medical history summary.
# Why it's structured this way: Separates healthcare-specific attributes from core authentication credentials (User model).
# Parameters & Returns: Django Model entity representing an individual patient's clinical baseline.
# ------------------------------------------------------------------------------
class PatientProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile",
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=30, blank=True)
    blood_group = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    medical_history_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Patient Profile"
        verbose_name_plural = "Patient Profiles"

    def __str__(self):
        return f"PatientProfile: {self.user.email}"

