# ==============================================================================
# FILE: backend/apps/accounts/views.py
# PURPOSE: Authentication API endpoints (Registration, Login, Token Refresh, Logout, and Current User profile).
# VIVA EXPLANATION: Provides secure JWT session lifecycle management with HIPAA audit logging on login/logout and strict role segregation between patients and doctors.
# ==============================================================================

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.audit_logs.services import log_audit_event
from apps.audit_logs.models import AuditLog

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
    MedicareTokenObtainPairSerializer,
    LogoutSerializer,
)
from .services import register_user, blacklist_refresh_token


# --- RegisterView ---
# What it does: Registers new patient accounts and generates initial JWT access/refresh token pairs.
# Why it's structured this way: Enforces input validation, hashes credentials, and logs patient onboarding audit events.
# Parameters & Returns: POST request with email, password, and optional demographic names; returns user profile and tokens.
# ------------------------------------------------------------------------------
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = register_user(serializer.validated_data, request=request)
        user_data = UserSerializer(result["user"]).data
        return Response(
            {
                "user": user_data,
                "tokens": result["tokens"],
                "message": "User registered successfully.",
            },
            status=status.HTTP_201_CREATED,
        )


# --- LoginView ---
# What it does: Authenticates email/password credentials and issues JWT token pairs embedding user roles.
# Why it's structured this way: Captures successful logins to emit regulatory AuditLog records with IP and timestamp.
# Parameters & Returns: POST with email and password; returns access and refresh JWT tokens.
# ------------------------------------------------------------------------------
class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = MedicareTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            email = request.data.get("email")
            from .models import User
            user = User.objects.filter(email__iexact=email).first()
            if user:
                log_audit_event(
                    user=user,
                    action=AuditLog.Actions.USER_LOGIN,
                    resource_type="User",
                    resource_id=user.id,
                    request=request,
                    metadata={"role": user.role},
                )
        return response


# --- LogoutView ---
# What it does: Invalidates active sessions by blacklisting the supplied JWT refresh token.
# Why it's structured this way: Prevents replay attacks and ensures terminated sessions cannot generate new access tokens.
# Parameters & Returns: POST with 'refresh' token string; returns HTTP 200 on success.
# ------------------------------------------------------------------------------
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            blacklist_refresh_token(
                serializer.validated_data["refresh"],
                user=request.user,
                request=request,
            )
            return Response(
                {"message": "Logged out successfully. Refresh token invalidated."},
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            return Response(
                {"error": {"code": "LOGOUT_FAILED", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )


# --- MeView ---
# What it does: Retrieves (GET) or partially updates (PATCH) the currently authenticated user's profile.
# Why it's structured this way: Automatically joins role-specific sub-profiles (PatientProfile or DoctorProfile).
# Parameters & Returns: GET returns full profile; PATCH updates first_name/last_name and returns updated User.
# ------------------------------------------------------------------------------
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = UserSerializer(user).data
        if user.role == user.Roles.PATIENT:
            if not hasattr(user, "patient_profile"):
                from apps.patients.models import PatientProfile
                PatientProfile.objects.get_or_create(user=user)
            from apps.patients.serializers import PatientProfileSerializer
            data["profile"] = PatientProfileSerializer(user.patient_profile).data
        elif user.role == user.Roles.DOCTOR:
            if not hasattr(user, "doctor_profile"):
                from apps.doctors.models import DoctorProfile
                DoctorProfile.objects.get_or_create(user=user)
            from apps.doctors.serializers import DoctorProfileSerializer
            data["profile"] = DoctorProfileSerializer(user.doctor_profile).data
        return Response(data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


# --- TokenRefreshCustomView ---
# What it does: SimpleJWT endpoint for exchanging an unexpired refresh token for a fresh access token.
# Why it's structured this way: Enables seamless frontend session renewal without logging the user out.
# Parameters & Returns: POST with 'refresh' token; returns new 'access' token string.
# ------------------------------------------------------------------------------
class TokenRefreshCustomView(TokenRefreshView):
    permission_classes = [AllowAny]
