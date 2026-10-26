# ==============================================================================
# FILE: backend/apps/medical_records/models.py
# PURPOSE: Relational data models for patient clinical records, uploaded diagnostic lab reports, and extracted biomarker results.
# VIVA EXPLANATION: This module models patient clinical documentation. MedicalRecord stores clinician notes and consultations, LabReport manages uploaded diagnostic documents with parsed OCR text, and LabResult tracks granular numerical biomarkers with biological reference ranges and clinical abnormality flags (e.g., normal, low, high, critical).
# ==============================================================================

import os
from django.conf import settings
from django.db import models
from core.utilities import generate_safe_filename


# --- report_upload_path ---
# What it does: Computes secure, unguessable file storage paths organized by date.
# Why it's structured this way: Prevents filename collision and protects against directory traversal attacks.
# Parameters & Returns: instance, filename -> relative file path string.
# ------------------------------------------------------------------------------
def report_upload_path(instance, filename):
    """Generates an unguessable safe server path for uploaded medical reports."""
    safe_name = generate_safe_filename(filename)
    return os.path.join("reports", "%Y", "%m", safe_name)


# --- MedicalRecord ---
# What it does: Captures physician consultation notes, diagnoses, and encounter timelines for a patient.
# Why it's structured this way: Indexed on patient and recorded_at for rapid electronic health record (EHR) timeline queries.
# Parameters & Returns: Django Model representing clinical encounters.
# ------------------------------------------------------------------------------
class MedicalRecord(models.Model):
    """
    Stores generalized patient clinical encounters, history, and physician notes.
    """
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="medical_records",
        help_text="Patient user associated with this clinical record.",
    )
    title = models.CharField(max_length=200, help_text="Clinical record title.")
    record_type = models.CharField(max_length=50, blank=True, help_text="Category (e.g. Consult, Surgery, History).")
    description = models.TextField(blank=True, help_text="Clinical narrative notes or findings.")
    recorded_at = models.DateTimeField(db_index=True, help_text="Date when clinical encounter took place.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["patient", "-recorded_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.patient.email})"


# --- LabReport ---
# What it does: Manages uploaded laboratory test documents, parsed OCR text, and AI clinical summaries.
# Why it's structured this way: Stores raw unstructured document alongside parsed text for medical record verification.
# Parameters & Returns: Django Model representing an uploaded lab report.
# ------------------------------------------------------------------------------
class LabReport(models.Model):
    """
    Stores diagnostic lab files (PDF, PNG, JPG) and parsed text.
    """
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lab_reports",
        help_text="Patient user whose laboratory tests were conducted.",
    )
    file = models.FileField(upload_to="reports/%Y/%m/", help_text="Uploaded laboratory document.")
    title = models.CharField(max_length=200, blank=True, help_text="Report title or test panel name.")
    file_type = models.CharField(max_length=50, blank=True, help_text="File extension (pdf, png, jpg).")
    file_size = models.PositiveIntegerField(default=0, help_text="File size in bytes.")
    extracted_text = models.TextField(blank=True, help_text="Plaintext extracted from PDF streams or OCR.")
    analysis_summary = models.TextField(blank=True, help_text="Automated clinical biomarker summary.")
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["patient", "-uploaded_at"]),
        ]

    def __str__(self):
        return f"LabReport: {self.title or self.file.name} ({self.patient.email})"


# --- LabResult ---
# What it does: Represents an individual quantitative biomarker (e.g. Glucose, HbA1c) extracted from a lab report.
# Why it's structured this way: Normalizes discrete clinical laboratory analytes to allow charting and longitudinal trend tracking.
# Parameters & Returns: Django Model representing a single biomarker test result.
# ------------------------------------------------------------------------------
class LabResult(models.Model):
    """
    Stores individual quantitative biomarker measurements extracted from a LabReport.
    """
    report = models.ForeignKey(
        LabReport,
        on_delete=models.CASCADE,
        related_name="results",
        help_text="Parent LabReport containing this test metric.",
    )
    test_name = models.CharField(max_length=150, help_text="Analyte name (e.g. Glucose, Hemoglobin, WBC).")
    value = models.CharField(max_length=100, help_text="Measured quantitative numerical value.")
    unit = models.CharField(max_length=50, blank=True, help_text="Measurement unit (e.g. mg/dL, g/dL, %).")
    reference_range = models.CharField(max_length=100, blank=True, help_text="Normal biological reference range.")
    flag = models.CharField(max_length=30, blank=True, help_text="Clinical flag: normal, low, high, critical.")

    class Meta:
        ordering = ["test_name"]

    def __str__(self):
        return f"{self.test_name}: {self.value} {self.unit} ({self.flag})"
