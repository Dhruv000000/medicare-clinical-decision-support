# ==============================================================================
# FILE: backend/apps/medicines/urls.py
# PURPOSE: URL routing configuration for medication management, OpenFDA intelligence, and interaction checks.
# VIVA EXPLANATION: Maps HTTP endpoints to medication views (/interactions/, /openfda/reactions/, /openfda/interactions/, and CRUD routes) under the /api/v1/medicines/ namespace.
# ==============================================================================

from django.urls import path
from .views import (
    MedicationListCreateView,
    MedicationDetailView,
    OpenFDAReactionsView,
    OpenFDAInteractionsView,
    MedicineInteractionView,
)

# --- urlpatterns ---
# What it does: Registers URL route handlers for prescriptions, adverse drug reaction lookups, and drug-drug interaction safety checks.
# Why it's structured this way: Follows RESTful URL conventions with specialized sub-paths for OpenFDA pharmacovigilance endpoints.
# Parameters & Returns: List of django.urls.path route objects.
# ------------------------------------------------------------------------------
urlpatterns = [
    path("", MedicationListCreateView.as_view(), name="medication-list-create"),
    path("<int:medication_id>/", MedicationDetailView.as_view(), name="medication-detail"),
    path("interactions/", MedicineInteractionView.as_view(), name="medicine-interactions"),
    path("openfda/reactions/", OpenFDAReactionsView.as_view(), name="openfda-reactions"),
    path("openfda/interactions/", OpenFDAInteractionsView.as_view(), name="openfda-interactions"),
]


