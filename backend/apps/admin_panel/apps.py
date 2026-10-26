# ==============================================================================
# FILE: backend/apps/admin_panel/apps.py
# PURPOSE: Application configuration metadata for the admin_panel app.
# VIVA EXPLANATION: Registers the administrative panel application module within Django.
# ==============================================================================

from django.apps import AppConfig


# --- AdminPanelConfig ---
# What it does: Sets default primary key field type and app module namespace.
# Why it's structured this way: Standard Django AppConfig subclass.
# Parameters & Returns: Django AppConfig definition.
# ------------------------------------------------------------------------------
class AdminPanelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.admin_panel"

