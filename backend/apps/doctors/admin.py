# ==============================================================================
# FILE: backend/apps/doctors/admin.py
# PURPOSE: Django administration configuration for doctor profiles and clinical consultation records.
# VIVA EXPLANATION: Configures administrative oversight in the Django Admin interface, allowing administrators to verify clinician medical licenses and inspect clinical notes with search and filtering.
# ==============================================================================

from django.contrib import admin
from .models import DoctorProfile, ClinicalNote


# --- DoctorProfileAdmin ---
# What it does: Admin console interface for inspecting and verifying doctor credentials.
# Why it's structured this way: Exposes verification flags and filters by specialty to support administrative credential audits.
# Parameters & Returns: Django ModelAdmin configuration.
# ------------------------------------------------------------------------------
@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "license_number", "specialization", "hospital", "is_verified", "created_at")
    list_filter = ("is_verified", "specialization")
    search_fields = ("user__email", "license_number", "hospital")
    readonly_fields = ("created_at", "updated_at")


# --- ClinicalNoteAdmin ---
# What it does: Admin console interface for reviewing clinical documentation notes between doctors and patients.
# Why it's structured this way: Keeps created_at and updated_at read-only to preserve medicolegal integrity of patient notes.
# Parameters & Returns: Django ModelAdmin configuration.
# ------------------------------------------------------------------------------
@admin.register(ClinicalNote)
class ClinicalNoteAdmin(admin.ModelAdmin):
    list_display = ("id", "doctor", "patient", "diagnosis", "created_at")
    search_fields = ("doctor__email", "patient__email", "diagnosis", "note")
    list_filter = ("created_at",)
    readonly_fields = ("created_at", "updated_at")

