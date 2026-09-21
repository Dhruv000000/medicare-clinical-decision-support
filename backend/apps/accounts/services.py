from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
from apps.audit_logs.services import log_audit_event
from apps.audit_logs.models import AuditLog
from .models import User


def register_user(validated_data, request=None):
    """
    Registers a new user inside an atomic transaction,
    automatically creates the role-specific profile (PatientProfile or DoctorProfile),
    and records an audit log event.
    """
    with transaction.atomic():
        role = validated_data.get("role", User.Roles.PATIENT)
        password = validated_data.pop("password")
        validated_data.pop("confirm_password", None)
        validated_data.pop("username", None)
        user = User.objects.create_user(password=password, **validated_data)

        # Create corresponding profile
        if role == User.Roles.PATIENT:
            from apps.patients.models import PatientProfile
            PatientProfile.objects.create(user=user)
        elif role == User.Roles.DOCTOR:
            from apps.doctors.models import DoctorProfile
            DoctorProfile.objects.create(user=user)

        # Audit log
        log_audit_event(
            user=user,
            action=AuditLog.Actions.USER_REGISTER,
            resource_type="User",
            resource_id=user.id,
            request=request,
            metadata={"role": user.role, "email": user.email},
        )

        refresh = RefreshToken.for_user(user)
        refresh["email"] = user.email
        refresh["role"] = user.role

        return {
            "user": user,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
        }


def blacklist_refresh_token(refresh_token_str, user=None, request=None):
    """
    Blacklists the provided refresh token and records an audit log event.
    """
    token = RefreshToken(refresh_token_str)
    token.blacklist()

    log_audit_event(
        user=user,
        action=AuditLog.Actions.USER_LOGOUT,
        resource_type="User",
        resource_id=user.id if user else "",
        request=request,
        metadata={"detail": "Refresh token successfully blacklisted"},
    )
