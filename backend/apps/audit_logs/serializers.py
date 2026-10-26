# ==============================================================================
# FILE: backend/apps/audit_logs/serializers.py
# PURPOSE: Read-only serializer for security audit trail log entries.
# VIVA EXPLANATION: Serializes immutable system event logs (action, resource, IP address, metadata JSON) for administrative review, ensuring that all log attributes remain read-only.
# ==============================================================================

from rest_framework import serializers
from .models import AuditLog


# --- AuditLogSerializer ---
# What it does: Converts AuditLog database records to read-only JSON payloads with user_email.
# Why it's structured this way: Locks down all fields as read-only to preserve legal integrity of audit records.
# Parameters & Returns: AuditLog model instance -> Read-only dictionary.
# ------------------------------------------------------------------------------
class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "user_email",
            "action",
            "resource_type",
            "resource_id",
            "ip_address",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields

