# ==============================================================================
# FILE: backend/apps/audit_logs/admin.py
# PURPOSE: Django administration configuration for security audit logs.
# VIVA EXPLANATION: Configures admin inspection of audit logs. Strictly disables manual addition and deletion permissions (has_add_permission=False, has_delete_permission=False) to guarantee that audit trails remain tamper-proof and immutable under HIPAA/GDPR rules.
# ==============================================================================

from django.contrib import admin
from .models import AuditLog


# --- AuditLogAdmin ---
# What it does: Admin console interface for viewing immutable security log entries.
# Why it's structured this way: Enforces write-once read-many (WORM) audit integrity by returning False for add/delete permissions.
# Parameters & Returns: Django ModelAdmin configuration.
# ------------------------------------------------------------------------------
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "action", "user", "resource_type", "resource_id", "ip_address", "created_at")
    list_filter = ("action", "resource_type", "created_at")
    search_fields = ("action", "resource_type", "resource_id", "user__email")
    readonly_fields = ("user", "action", "resource_type", "resource_id", "ip_address", "metadata", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

