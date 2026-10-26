# ==============================================================================
# FILE: backend/config/urls.py
# PURPOSE: Root URL dispatcher configuring top-level API routes and health check probes.
# VIVA EXPLANATION: The master routing table of the Django REST application. Mounts the canonical /api/v1/ prefix for all domain micro-apps (auth, patient, doctor, admin, appointments, medical records, predictions, medicines, and AI assistant) and serves health check telemetry.
# ==============================================================================

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from core.utilities import check_database_connection


# --- HealthCheckView ---
# What it does: GET /api/v1/health/ - Liveness and readiness probe for container orchestration and uptime monitoring.
# Why it's structured this way: Safely tests database connectivity via check_database_connection and returns 200 OK or 503 Service Unavailable.
# Parameters & Returns: GET request -> Health status JSON payload.
# ------------------------------------------------------------------------------
class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        db_info = check_database_connection()
        is_healthy = db_info.get("status") == "connected"

        payload = {
            "status": "ok" if is_healthy else "degraded",
            "service": "medicare-api",
            "version": "1.0.0",
            "database": {
                "status": db_info.get("status"),
                "vendor": db_info.get("vendor"),
            },
        }

        http_status = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(payload, status=http_status)


urlpatterns = [
    # Django Admin Site
    path("admin/", admin.site.urls),

    # Health Check Endpoint
    path("api/v1/health/", HealthCheckView.as_view(), name="api-health"),

    # Canonical API v1 Routes (Correction 7)
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/patient/", include("apps.patients.urls")),
    path("api/v1/doctor/", include("apps.doctors.urls")),
    path("api/v1/admin/", include("apps.admin_panel.urls")),
    path("api/v1/appointments/", include("apps.appointments.urls")),
    path("api/v1/records/", include("apps.medical_records.urls")),
    path("api/v1/medical-records/", include("apps.medical_records.urls")),
    path("api/v1/predictions/", include("apps.predictions.urls")),
    path("api/v1/medicines/", include("apps.medicines.urls")),
    path("api/v1/assistant/", include("apps.assistant.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

