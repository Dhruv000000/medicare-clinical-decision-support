# ==============================================================================
# FILE: backend/apps/appointments/models.py
# PURPOSE: Clinical appointment scheduling model between patients and licensed physicians.
# VIVA EXPLANATION: Represents clinical encounters with lifecycle states (Scheduled, Confirmed, Completed, Cancelled); also establishes the legal doctor-patient authorization relationship required for clinical record access.
# ==============================================================================

from django.conf import settings
from django.db import models


# --- Appointment ---
# What it does: Stores scheduled clinical consultations linking a patient User and doctor User with date/time, chief complaint, and status.
# Why it's structured this way: Indexes (patient, status, starts_at) and (doctor, status, starts_at) for fast schedule lookups, and serves as an authority boundary anchor.
# Parameters & Returns: Django Appointment model.
# ------------------------------------------------------------------------------
class Appointment(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_appointments",
        help_text="Patient receiving the clinical consultation.",
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_appointments",
        help_text="Doctor conducting the appointment.",
    )
    starts_at = models.DateTimeField(db_index=True, help_text="Scheduled appointment start time.")
    reason = models.TextField(blank=True, help_text="Chief complaint or reason for consultation.")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        db_index=True,
        help_text="Current lifecycle state of the appointment.",
    )
    notes = models.TextField(blank=True, help_text="Clinical preparation or follow-up notes.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at"]
        indexes = [
            models.Index(fields=["patient", "status", "starts_at"]),
            models.Index(fields=["doctor", "status", "starts_at"]),
        ]

    def __str__(self):
        return f"Appointment: {self.patient.email} with Dr. {self.doctor.email} at {self.starts_at}"
