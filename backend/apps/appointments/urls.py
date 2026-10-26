# ==============================================================================
# FILE: backend/apps/appointments/urls.py
# PURPOSE: URL routing configuration for clinical appointment endpoints.
# VIVA EXPLANATION: Exposes collection endpoints for listing/booking appointments and detail endpoints for appointment retrieval and status transitions.
# ==============================================================================

from django.urls import path
from .views import AppointmentListCreateView, AppointmentDetailView

urlpatterns = [
    path("", AppointmentListCreateView.as_view(), name="appointment-list-create"),
    path("<int:appointment_id>/", AppointmentDetailView.as_view(), name="appointment-detail"),
]
