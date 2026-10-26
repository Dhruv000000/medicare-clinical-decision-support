# ==============================================================================
# FILE: backend/apps/patients/apps.py
# PURPOSE: Application configuration metadata for the patients app.
# VIVA EXPLANATION: Registers the patient management domain within Django's application registry.
# ==============================================================================

from django.apps import AppConfig


# --- PatientsConfig ---
# What it does: Sets default primary key field type and app module namespace.
# Why it's structured this way: Standard Django AppConfig subclass.
# Parameters & Returns: Django AppConfig definition.
# ------------------------------------------------------------------------------
class PatientsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.patients"

