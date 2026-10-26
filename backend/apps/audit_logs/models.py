# ==============================================================================
# FILE: backend/apps/audit_logs/models.py
# PURPOSE: Regulatory immutable audit trail model tracking all clinical data events and authentication activities.
# VIVA EXPLANATION: Implements HIPAA-compliant access auditing; records user IDs, IP addresses, action types, resource references, and JSON metadata with read-only database indexes.
# ==============================================================================

from django.conf import settings
from django.db import models


# --- AuditLog ---
# What it does: Stores an immutable security log entry for clinical actions, user logins, report uploads, and predictions.
# Why it's structured this way: Enforces traceability—retains SET_NULL on user deletion so historical forensic records are preserved even if an account is removed.
# Parameters & Returns: Django AuditLog model.
# ------------------------------------------------------------------------------
class AuditLog(models.Model):
    class Actions(models.TextChoices):
        USER_REGISTER = "USER_REGISTER", "User Registration"
        USER_LOGIN = "USER_LOGIN", "User Login"
        USER_LOGOUT = "USER_LOGOUT", "User Logout"
        TOKEN_REFRESH = "TOKEN_REFRESH", "Token Refresh"
        REPORT_UPLOAD = "REPORT_UPLOAD", "Lab Report Upload"
        RECORD_CREATE = "RECORD_CREATE", "Medical Record Create"
        RECORD_UPDATE = "RECORD_UPDATE", "Medical Record Update"
        APPOINTMENT_CREATE = "APPOINTMENT_CREATE", "Appointment Create"
        APPOINTMENT_UPDATE = "APPOINTMENT_UPDATE", "Appointment Update"
        CLINICAL_NOTE_CREATE = "CLINICAL_NOTE_CREATE", "Clinical Note Create"
        ADMIN_USER_UPDATE = "ADMIN_USER_UPDATE", "Admin User Update"
        ADMIN_ACCESS = "ADMIN_ACCESS", "Admin Access"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        help_text="User who initiated the action (retained as null if user is deleted).",
    )
    action = models.CharField(max_length=100, db_index=True, help_text="Action category identifier.")
    resource_type = models.CharField(max_length=100, blank=True, db_index=True, help_text="Target entity type.")
    resource_id = models.CharField(max_length=100, blank=True, help_text="Target primary key.")
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="Client IP address.")
    metadata = models.JSONField(default=dict, blank=True, help_text="Detailed contextual state changes.")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, help_text="Immutable log timestamp.")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action", "-created_at"]),
            models.Index(fields=["resource_type", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        actor = self.user.email if self.user else "Anonymous"
        return f"[{self.created_at:%Y-%m-%d %H:%M:%S}] {actor} - {self.action}"
