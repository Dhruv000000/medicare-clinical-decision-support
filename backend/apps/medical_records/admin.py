# ==============================================================================
# FILE: backend/apps/medical_records/admin.py
# PURPOSE: Django administration configuration for EHR medical records, lab reports, and biomarker results.
# VIVA EXPLANATION: Configures Django admin panels for clinical documentation, featuring TabularInline biomarker result viewing and read-only audit timestamp fields.
# ==============================================================================

from django.contrib import admin
from .models import MedicalRecord, LabReport, LabResult


# --- LabResultInline ---
# What it does: Inlines child biomarker test results directly inside the parent LabReport admin view.
# Why it's structured this way: Provides clinicians and administrators with an instant view of all analytes without clicking into separate detail pages.
# Parameters & Returns: TabularInline subclass.
# ------------------------------------------------------------------------------
class LabResultInline(admin.TabularInline):
    model = LabResult
    extra = 0


# --- MedicalRecordAdmin ---
# What it does: Registers MedicalRecord model with filtering by record_type and patient search.
# Why it's structured this way: Read-only created_at and updated_at ensure clinical note tamper-evidence.
# Parameters & Returns: Django ModelAdmin subclass.
# ------------------------------------------------------------------------------
@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "title", "record_type", "recorded_at", "created_at")
    list_filter = ("record_type", "recorded_at")
    search_fields = ("patient__email", "title", "description")
    readonly_fields = ("created_at", "updated_at")


# --- LabReportAdmin ---
# What it does: Admin panel for diagnostic lab documents with nested LabResultInline display.
# Why it's structured this way: Displays document metadata alongside parsed biochemical values.
# Parameters & Returns: Django ModelAdmin subclass.
# ------------------------------------------------------------------------------
@admin.register(LabReport)
class LabReportAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "title", "file_type", "file_size", "uploaded_at")
    list_filter = ("file_type", "uploaded_at")
    search_fields = ("patient__email", "title", "file")
    readonly_fields = ("uploaded_at",)
    inlines = [LabResultInline]


# --- LabResultAdmin ---
# What it does: Standalone admin panel for discrete quantitative biomarker test results.
# Why it's structured this way: Allows administrative searching and filtering across specific test names (e.g. Glucose).
# Parameters & Returns: Django ModelAdmin subclass.
# ------------------------------------------------------------------------------
@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ("id", "report", "test_name", "value", "unit", "reference_range", "flag")
    search_fields = ("test_name", "report__patient__email")

