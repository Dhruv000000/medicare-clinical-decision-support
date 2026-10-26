# ==============================================================================
# FILE: backend/apps/medicines/models.py
# PURPOSE: Relational data model for patient medications and electronic prescriptions.
# VIVA EXPLANATION: Represents active and historical patient prescriptions. Tracks medication names, dosages, administration frequencies, prescribing clinician, and active status indexed for rapid multi-drug safety checks.
# ==============================================================================

from django.conf import settings
from django.db import models


# --- Medication ---
# What it does: Stores prescribed drugs with dosages, schedules, prescribing doctor, and active status flags.
# Why it's structured this way: Indexed on (patient, is_active) to optimize pharmacovigilance and drug interaction lookup queries.
# Parameters & Returns: Django Model representing a prescription.
# ------------------------------------------------------------------------------
class Medication(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="medications",
    )
    name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100, blank=True)
    frequency = models.CharField(max_length=100, blank=True)
    prescribed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescribed_medications",
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_active", "-created_at"]
        indexes = [
            models.Index(fields=["patient", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} for {self.patient.email}"
