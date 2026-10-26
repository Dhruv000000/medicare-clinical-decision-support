# ==============================================================================
# FILE: backend/apps/predictions/urls.py
# PURPOSE: URL routing configuration for clinical disease predictions and symptom analysis endpoints.
# VIVA EXPLANATION: Maps HTTP endpoints to prediction views (/disease/, /symptoms/, and root listing), routing client requests to the clean prediction controller layer.
# ==============================================================================

from django.urls import path
from .views import (
    PredictionListView,
    SymptomAnalysisListView,
    DiseasePredictionCreateView,
)

# --- urlpatterns ---
# What it does: Registers URL route handlers for prediction history, symptom NLP analysis, and AI disease diagnosis.
# Why it's structured this way: Follows RESTful URL conventions under the /api/v1/predictions/ namespace.
# Parameters & Returns: List of django.urls.path route objects.
# ------------------------------------------------------------------------------
urlpatterns = [
    path("", PredictionListView.as_view(), name="prediction-list"),
    path("symptoms/", SymptomAnalysisListView.as_view(), name="symptom-analysis-list"),
    path("disease/", DiseasePredictionCreateView.as_view(), name="disease-prediction-create"),
]

