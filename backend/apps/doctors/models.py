# ==============================================================================
# FILE: backend/apps/doctors/models.py
# PURPOSE: Relational data models for physician profiles and clinical consultation notes.
# VIVA EXPLANATION: Implements clinician modeling in MediCare. DoctorProfile tracks medical licenses, specialties, and hospital affiliations, while ClinicalNote stores physician diagnostic notes linked to patients and indexed for clinical audit trails.
# ==============================================================================

from django.conf import settings
from django.db import models


# --- DoctorProfile ---
# What it does: Stores clinician credentials, medical license number, verification status, and hospital affiliation.
# Why it's structured this way: OneToOne relationship with User separates general auth from clinical credential management.
# Parameters & Returns: Django Model representing doctor credentials.
# ------------------------------------------------------------------------------
class DoctorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_profile",
    )
    license_number = models.CharField(max_length=100, unique=True, null=True, blank=True)
    specialization = models.CharField(max_length=100, blank=True)
    hospital = models.CharField(max_length=200, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Doctor Profile"
        verbose_name_plural = "Doctor Profiles"

    def __str__(self):
        spec = f" - {self.specialization}" if self.specialization else ""
        return f"Dr. {self.user.first_name} {self.user.last_name} ({self.user.email}){spec}"


# --- ClinicalNote ---
# What it does: Records doctor clinical consultation notes, provisional diagnoses, and therapeutic guidance.
# Why it's structured this way: Indexed on (doctor, patient, -created_at) for efficient patient chart reviews and EHR timeline rendering.
# Parameters & Returns: Django Model representing clinical notes.
# ------------------------------------------------------------------------------
class ClinicalNote(models.Model):
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="authored_clinical_notes",
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_clinical_notes",
    )
    diagnosis = models.CharField(max_length=255, blank=True)
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["doctor", "patient", "-created_at"]),
        ]

    def __str__(self):
        return f"Clinical Note by {self.doctor.email} for {self.patient.email} at {self.created_at:%Y-%m-%d}"
