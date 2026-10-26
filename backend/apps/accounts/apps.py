# ==============================================================================
# FILE: backend/apps/accounts/apps.py
# PURPOSE: Django application configuration for the accounts authentication domain.
# VIVA EXPLANATION: Registers the accounts app with the Django application registry and configures auto field defaults.
# ==============================================================================

from django.apps import AppConfig


# --- AccountsConfig ---
# What it does: Declares app configuration metadata for the accounts module.
# Why it's structured this way: Follows Django standard application registry conventions.
# Parameters & Returns: None.
# ------------------------------------------------------------------------------
class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"

