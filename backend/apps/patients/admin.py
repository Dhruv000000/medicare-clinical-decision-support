# ==============================================================================
# FILE: backend/apps/patients/admin.py
# PURPOSE: Django administration configuration for patient profiles.
# VIVA EXPLANATION: Configures admin console views for patient demographic records, supporting filtering by gender/blood group and searching by email or emergency contact.
# ==============================================================================

from django.contrib import admin
from .models import PatientProfile


# --- PatientProfileAdmin ---
# What it does: Admin console configuration for inspecting patient profiles.
# Why it's structured this way: Provides administrative overview with immutable timestamp tracking.
# Parameters & Returns: Django ModelAdmin configuration.
# ------------------------------------------------------------------------------
@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "gender", "blood_group", "phone", "created_at")
    search_fields = ("user__email", "phone", "emergency_contact")
    list_filter = ("gender", "blood_group")
    readonly_fields = ("created_at", "updated_at")

