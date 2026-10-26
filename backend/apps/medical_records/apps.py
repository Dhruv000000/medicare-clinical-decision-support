# ==============================================================================
# FILE: backend/apps/medical_records/apps.py
# PURPOSE: Django application configuration for patient medical records and lab reports.
# VIVA EXPLANATION: Configures application metadata and models registry for patient health documents and laboratory biomarker results.
# ==============================================================================

from django.apps import AppConfig


# --- MedicalRecordsConfig ---
# What it does: Registers the medical records application within Django.
# Why it's structured this way: Follows standard Django AppConfig conventions.
# Parameters & Returns: None.
# ------------------------------------------------------------------------------
class MedicalRecordsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.medical_records"

