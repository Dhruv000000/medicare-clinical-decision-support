# ==============================================================================
# FILE: backend/apps/appointments/admin.py
# PURPOSE: Django Admin panel configuration for managing patient-doctor clinical appointments.
# VIVA EXPLANATION: Configures administrative appointment viewing with search by patient/doctor email and filtering by lifecycle status and date.
# ==============================================================================

from django.contrib import admin
from .models import Appointment


# --- AppointmentAdmin ---
# What it does: Registers the Appointment model with searchable columns and status filter facets.
# Why it's structured this way: Facilitates clinic administration and schedule auditing.
# Parameters & Returns: Django ModelAdmin class.
# ------------------------------------------------------------------------------
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "doctor", "starts_at", "status", "created_at")
    list_filter = ("status", "starts_at", "created_at")
    search_fields = ("patient__email", "doctor__email", "reason", "notes")
    readonly_fields = ("created_at", "updated_at")
