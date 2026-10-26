# ==============================================================================
# FILE: backend/apps/accounts/serializers.py
# PURPOSE: DRF serializers for user registration, profile retrieval/updates, and JWT claims.
# VIVA EXPLANATION: Handles user onboarding validation (password strength, email normalization), prevents privilege escalation on profile edits, and embeds role claims into SimpleJWT tokens.
# ==============================================================================

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User


# --- UserSerializer ---
# What it does: Serializes public User information and resolves the associated profile_id (patient or doctor).
# Why it's structured this way: Read-only representation ensuring security fields (passwords, role, is_active) cannot be tampered with.
# Parameters & Returns: Returns serialized User dictionary.
# ------------------------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    profile_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "profile_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "email", "role", "is_active", "created_at", "updated_at"]

    def get_profile_id(self, obj):
        if obj.role == User.Roles.PATIENT and hasattr(obj, "patient_profile"):
            return obj.patient_profile.id
        elif obj.role == User.Roles.DOCTOR and hasattr(obj, "doctor_profile"):
            return obj.doctor_profile.id
        return None


# --- RegisterSerializer ---
# What it does: Validates patient registration inputs, enforces password policies, and creates new User instances.
# Why it's structured this way: Ensures email uniqueness, matches password confirmations, and securely hashes credentials.
# Parameters & Returns: Takes registration dictionary; returns newly created User instance.
# ------------------------------------------------------------------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    username = serializers.CharField(write_only=True, required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")
    role = serializers.CharField(required=False, default=User.Roles.PATIENT)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "confirm_password",
            "username",
            "first_name",
            "last_name",
            "role",
        ]

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate_role(self, value):
        if not value:
            return User.Roles.PATIENT
        val = str(value).lower().strip()
        valid_roles = [c[0] for c in User.Roles.choices]
        if val not in valid_roles:
            raise serializers.ValidationError(
                f"Invalid role '{value}'. Must be one of: {', '.join(valid_roles)}."
            )
        return val

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")
        if confirm_password and password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("confirm_password", None)
        validated_data.pop("username", None)
        user = User.objects.create_user(password=password, **validated_data)
        return user


# --- UserUpdateSerializer ---
# What it does: Sanitizes PATCH updates to the authenticated user's own profile.
# Why it's structured this way: Whitelists only 'first_name' and 'last_name', strictly blocking privilege escalation to 'admin' or role tampering.
# Parameters & Returns: Updates first_name and last_name of User instance.
# ------------------------------------------------------------------------------
class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Used for PATCH /api/v1/auth/me/.
    Strictly prevents modifying role, email, is_staff, is_superuser, etc. (Correction 11).
    """

    class Meta:
        model = User
        fields = ["first_name", "last_name"]


# --- MedicareTokenObtainPairSerializer ---
# What it does: Custom SimpleJWT serializer embedding email and role enums in the token claims and response body.
# Why it's structured this way: Allows frontend React clients to immediately inspect user role without making additional round-trip API queries.
# Parameters & Returns: Returns standard JWT tokens (access, refresh) plus user profile payload.
# ------------------------------------------------------------------------------
class MedicareTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that embeds user email and application role directly in the token payload.
    Supports validating role if role is submitted from client login forms.
    """
    role = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        requested_role = self.initial_data.get("role") or attrs.get("role")
        if requested_role:
            req_role = str(requested_role).strip().lower()
            user_role = str(self.user.role).strip().lower()
            if user_role != req_role:
                raise serializers.ValidationError(
                    {
                        "role": f"Access denied. This account has the role '{self.user.role}', but login was requested for '{req_role}'."
                    }
                )

        profile_id = None
        if self.user.role == User.Roles.PATIENT and hasattr(self.user, "patient_profile"):
            profile_id = self.user.patient_profile.id
        elif self.user.role == User.Roles.DOCTOR and hasattr(self.user, "doctor_profile"):
            profile_id = self.user.doctor_profile.id

        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "role": self.user.role,
            "profile_id": profile_id,
        }
        return data



# --- LogoutSerializer ---
# What it does: Validates that a refresh token is structurally well-formed before blacklisting.
# Why it's structured this way: Enables secure session invalidation and token blacklisting on user logout.
# Parameters & Returns: Validates 'refresh' string parameter.
# ------------------------------------------------------------------------------
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)

    def validate_refresh(self, value):
        try:
            RefreshToken(value)
        except Exception:
            raise serializers.ValidationError("Invalid or expired refresh token.")
        return value
