# ==============================================================================
# FILE: backend/apps/appointments/apps.py
# PURPOSE: Django application configuration for the appointments scheduling module.
# VIVA EXPLANATION: Configures application metadata and models registry for patient-provider appointment bookings.
# ==============================================================================

from django.apps import AppConfig


# --- AppointmentsConfig ---
# What it does: Registers the appointments application within Django.
# Why it's structured this way: Follows standard Django AppConfig conventions.
# Parameters & Returns: None.
# ------------------------------------------------------------------------------
class AppointmentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.appointments"

