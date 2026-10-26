# ==============================================================================
# FILE: backend/apps/patients/views.py
# PURPOSE: REST API views for patient self-service profile and aggregated dashboard telemetry.
# VIVA EXPLANATION: Implements the patient portal backend. Restricts access to IsPatient users. ProfileView allows viewing and updating demographic records; DashboardView aggregates active prescriptions, appointments, records, and lab tests into a single low-latency call.
# ==============================================================================

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from core.permissions import IsPatient
from .models import PatientProfile
from .serializers import PatientProfileSerializer
from .services import get_patient_dashboard_data


# --- ProfileView ---
# What it does: GET retrieves patient personal details; PATCH performs partial updates on demographics.
# Why it's structured this way: Uses get_or_create to automatically initialize a profile if none exists for a new user.
# Parameters & Returns: GET/PATCH request -> Serialized PatientProfile data.
# ------------------------------------------------------------------------------
class ProfileView(APIView):
    permission_classes = [IsPatient]

    def get(self, request):
        profile, _ = PatientProfile.objects.get_or_create(user=request.user)
        serializer = PatientProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        profile, _ = PatientProfile.objects.get_or_create(user=request.user)
        serializer = PatientProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


# --- DashboardView ---
# What it does: GET /api/v1/patient/dashboard/ - Assembles a complete clinical overview for the authenticated patient.
# Why it's structured this way: Consolidates cross-domain counts (appointments, medications, reports) to reduce frontend network roundtrips.
# Parameters & Returns: Authenticated request -> JSON dictionary with upcoming appointments, active meds, and recent logs.
# ------------------------------------------------------------------------------
class DashboardView(APIView):
    permission_classes = [IsPatient]

    def get(self, request):
        data = get_patient_dashboard_data(request.user)
        return Response(data, status=status.HTTP_200_OK)

