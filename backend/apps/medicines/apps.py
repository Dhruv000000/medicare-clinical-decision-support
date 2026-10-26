# ==============================================================================
# FILE: backend/apps/medicines/apps.py
# PURPOSE: Django application configuration for pharmaceutical prescriptions and OpenFDA integration.
# VIVA EXPLANATION: Registers the medicines application within Django and configures models for prescription tracking and drug-drug interaction safety checks.
# ==============================================================================

from django.apps import AppConfig


# --- MedicinesConfig ---
# What it does: Registers the medicines application within Django.
# Why it's structured this way: Follows standard Django AppConfig conventions.
# Parameters & Returns: None.
# ------------------------------------------------------------------------------
class MedicinesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.medicines"

