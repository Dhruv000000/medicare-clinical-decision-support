# ==============================================================================
# FILE: backend/apps/predictions/admin.py
# PURPOSE: Django administration panel configuration for disease predictions and symptom logs.
# VIVA EXPLANATION: Configures Django admin interfaces for clinical audit review of machine learning predictions and raw patient symptom submissions with read-only timestamp protection.
# ==============================================================================

from django.contrib import admin
from .models import DiseasePrediction, SymptomAnalysis


# --- DiseasePredictionAdmin ---
# What it does: Registers DiseasePrediction model with filtering by model_name and search by patient email.
# Why it's structured this way: Read-only created_at guarantees timestamp integrity for regulatory auditability.
# Parameters & Returns: Django ModelAdmin subclass.
# ------------------------------------------------------------------------------
@admin.register(DiseasePrediction)
class DiseasePredictionAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "model_name", "predicted_condition", "confidence", "created_at")
    list_filter = ("model_name", "created_at")
    search_fields = ("patient__email", "predicted_condition", "model_name")
    readonly_fields = ("created_at",)


# --- SymptomAnalysisAdmin ---
# What it does: Registers SymptomAnalysis model with patient search capabilities.
# Why it's structured this way: Allows staff to review NLP parsing logs without modifying historical patient records.
# Parameters & Returns: Django ModelAdmin subclass.
# ------------------------------------------------------------------------------
@admin.register(SymptomAnalysis)
class SymptomAnalysisAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "created_at")
    search_fields = ("patient__email", "symptoms_text")
    readonly_fields = ("created_at",)

