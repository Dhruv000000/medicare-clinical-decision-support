# ==============================================================================
# FILE: backend/apps/assistant/apps.py
# PURPOSE: Django application configuration for the PubMed-grounded AI assistant module.
# VIVA EXPLANATION: Configures application metadata and models registry for RAG chat conversations and scientific literature citation caching.
# ==============================================================================

from django.apps import AppConfig


# --- AssistantConfig ---
# What it does: Registers the assistant application within Django.
# Why it's structured this way: Follows standard Django AppConfig conventions.
# Parameters & Returns: None.
# ------------------------------------------------------------------------------
class AssistantConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.assistant"

