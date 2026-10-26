# ==============================================================================
# FILE: backend/apps/predictions/apps.py
# PURPOSE: Django application configuration for machine learning predictions and explainability records.
# VIVA EXPLANATION: Configures application metadata and models registry for storing disease prediction outputs, TreeSHAP attributions, and symptom analyses.
# ==============================================================================

from django.apps import AppConfig


# --- PredictionsConfig ---
# What it does: Registers the predictions application within Django.
# Why it's structured this way: Follows standard Django AppConfig conventions.
# Parameters & Returns: None.
# ------------------------------------------------------------------------------
class PredictionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.predictions"

