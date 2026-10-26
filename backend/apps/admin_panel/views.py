# ==============================================================================
# FILE: backend/apps/admin_panel/views.py
# PURPOSE: Administrative portal controllers for user management, system audit log inspection, and system metrics.
# VIVA EXPLANATION: Implements the system administrator back-office APIs guarded by IsAdmin. Exposes paginated user directory management (enabling account activation/role changes), security audit trail querying, and database-wide operational analytics.
# ==============================================================================

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from core.permissions import IsAdmin
from core.pagination import StandardResultsSetPagination
from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer
from apps.appointments.models import Appointment
from apps.medical_records.models import MedicalRecord, LabReport
from apps.medicines.models import Medication
from apps.audit_logs.models import AuditLog
from apps.audit_logs.serializers import AuditLogSerializer
from apps.audit_logs.services import log_audit_event


# --- AdminUsersView ---
# What it does: GET lists registered users with optional role and status filters with pagination.
# Why it's structured this way: Allows administrative staff to browse and filter platform accounts securely.
# Parameters & Returns: GET request with query params (?role=doctor, ?is_active=true) -> Paginated UserSerializer results.
# ------------------------------------------------------------------------------
class AdminUsersView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        queryset = User.objects.all().order_by("-created_at")

        role_filter = request.query_params.get("role")
        if role_filter:
            queryset = queryset.filter(role=role_filter)

        active_filter = request.query_params.get("is_active")
        if active_filter is not None:
            queryset = queryset.filter(is_active=active_filter.lower() == "true")

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = UserSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# --- AdminUserDetailView ---
# What it does: PATCH modifies user account privileges, active flags, or user names, recording an audit log event.
# Why it's structured this way: Whitelists allowed mutable fields and validates roles against User.Roles enum to maintain DB integrity.
# Parameters & Returns: user_id URL param, PATCH body with updates -> Serialized UserSerializer response.
# ------------------------------------------------------------------------------
class AdminUserDetailView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, user_id):
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise NotFound(f"User with ID {user_id} not found.")

        # Admin can toggle is_active, update role, etc.
        allowed_fields = ["is_active", "role", "first_name", "last_name"]
        updates = {}
        for field in allowed_fields:
            if field in request.data:
                updates[field] = request.data[field]

        if "role" in updates and updates["role"] not in User.Roles.values:
            raise ValidationError(f"Invalid role. Choices: {User.Roles.values}")

        for k, v in updates.items():
            setattr(target_user, k, v)
        target_user.save()

        log_audit_event(
            user=request.user,
            action=AuditLog.Actions.ADMIN_USER_UPDATE,
            resource_type="User",
            resource_id=target_user.id,
            request=request,
            metadata={"updated_fields": list(updates.keys())},
        )

        return Response(UserSerializer(target_user).data, status=status.HTTP_200_OK)


# --- AdminAuditLogsView ---
# What it does: GET /api/v1/admin/audit-logs/ - Returns immutable chronological security and compliance log records.
# Why it's structured this way: Supports forensic audits and compliance monitoring filtered by action and resource type.
# Parameters & Returns: Query params (?action=..., ?resource_type=...) -> Paginated AuditLogSerializer items.
# ------------------------------------------------------------------------------
class AdminAuditLogsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        queryset = AuditLog.objects.select_related("user").all()

        action_filter = request.query_params.get("action")
        if action_filter:
            queryset = queryset.filter(action=action_filter)

        resource_filter = request.query_params.get("resource_type")
        if resource_filter:
            queryset = queryset.filter(resource_type=resource_filter)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AuditLogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# --- AdminAnalyticsView ---
# What it does: GET /api/v1/admin/analytics/ - Compiles real-time metrics across users, appointments, and medical records.
# Why it's structured this way: Runs live relational database aggregations to provide administrators with platform telemetry.
# Parameters & Returns: GET request -> Consolidated JSON object containing user, appointment, and clinical statistics.
# ------------------------------------------------------------------------------
class AdminAnalyticsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        # Users counts
        total_users = User.objects.count()
        patients_count = User.objects.filter(role=User.Roles.PATIENT).count()
        doctors_count = User.objects.filter(role=User.Roles.DOCTOR).count()
        admins_count = User.objects.filter(role=User.Roles.ADMIN).count()
        active_users_count = User.objects.filter(is_active=True).count()

        # Appointments breakdown
        total_appointments = Appointment.objects.count()
        appointments_by_status = {
            "scheduled": Appointment.objects.filter(status=Appointment.Status.SCHEDULED).count(),
            "confirmed": Appointment.objects.filter(status=Appointment.Status.CONFIRMED).count(),
            "completed": Appointment.objects.filter(status=Appointment.Status.COMPLETED).count(),
            "cancelled": Appointment.objects.filter(status=Appointment.Status.CANCELLED).count(),
        }

        # Clinical records
        medical_records_count = MedicalRecord.objects.count()
        lab_reports_count = LabReport.objects.count()
        medications_count = Medication.objects.count()
        audit_logs_count = AuditLog.objects.count()

        data = {
            "users": {
                "total": total_users,
                "patients": patients_count,
                "doctors": doctors_count,
                "admins": admins_count,
                "active": active_users_count,
            },
            "appointments": {
                "total": total_appointments,
                "by_status": appointments_by_status,
            },
            "clinical_data": {
                "medical_records": medical_records_count,
                "lab_reports": lab_reports_count,
                "medications": medications_count,
                "audit_logs_count": audit_logs_count,
            },
        }

        return Response(data, status=status.HTTP_200_OK)

