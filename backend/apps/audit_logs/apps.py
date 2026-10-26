# ==============================================================================
# FILE: backend/apps/audit_logs/apps.py
# PURPOSE: Application configuration metadata for the audit_logs app.
# VIVA EXPLANATION: Registers the security and compliance auditing module within Django.
# ==============================================================================

from django.apps import AppConfig


# --- AuditLogsConfig ---
# What it does: Configures default primary key types and app module namespace.
# Why it's structured this way: Standard Django AppConfig subclass.
# Parameters & Returns: Django AppConfig definition.
# ------------------------------------------------------------------------------
class AuditLogsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audit_logs"

