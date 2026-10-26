# ==============================================================================
# FILE: backend/apps/doctors/apps.py
# PURPOSE: Application configuration metadata for the doctors app.
# VIVA EXPLANATION: Registers the doctor management module within Django's application registry.
# ==============================================================================

from django.apps import AppConfig


# --- DoctorsConfig ---
# What it does: Configures default primary key types and app package namespace.
# Why it's structured this way: Standard Django AppConfig subclass for apps.doctors.
# Parameters & Returns: Django AppConfig definition.
# ------------------------------------------------------------------------------
class DoctorsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.doctors"

