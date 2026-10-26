# ==============================================================================
# FILE: backend/apps/medicines/admin.py
# PURPOSE: Django administration configuration for patient medications and prescriptions.
# VIVA EXPLANATION: Configures administrative oversight for medications, supporting status filters (active/discontinued) and full-text search across medicine names and patient emails.
# ==============================================================================

from django.contrib import admin
from .models import Medication


# --- MedicationAdmin ---
# What it does: Admin interface displaying medication name, patient, dosage, frequency, and active status.
# Why it's structured this way: Allows clinical and administrative auditing of active pharmacological treatments.
# Parameters & Returns: Django ModelAdmin subclass.
# ------------------------------------------------------------------------------
@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "patient", "dosage", "frequency", "is_active", "start_date", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "patient__email", "dosage")

