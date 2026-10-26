# ==============================================================================
# FILE: backend/apps/accounts/permissions.py
# PURPOSE: Role-based access control (RBAC) permissions for patients, doctors, and administrators.
# VIVA EXPLANATION: Implements granular permission classes verifying authenticated user roles against User.Roles enum, protecting sensitive medical records and clinical endpoints from unauthorized cross-role access.
# ==============================================================================

from rest_framework.permissions import BasePermission
from .models import User


# --- IsPatient ---
# What it does: Restricts endpoint access strictly to authenticated patient accounts.
# Why it's structured this way: Enforces role boundaries so clinicians or unauthorized roles cannot masquerade as patients.
# Parameters & Returns: request, view. Returns boolean.
# ------------------------------------------------------------------------------
class IsPatient(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Roles.PATIENT)


# --- IsDoctor ---
# What it does: Restricts endpoint access strictly to authenticated doctor accounts.
# Why it's structured this way: Safeguards clinical charting, prescription issuance, and lab analysis triggers.
# Parameters & Returns: request, view. Returns boolean.
# ------------------------------------------------------------------------------
class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Roles.DOCTOR)


# --- IsAdminRole ---
# What it does: Restricts endpoint access strictly to authenticated platform administrators.
# Why it's structured this way: Protects system audit trails, user account deactivation, and global telemetry.
# Parameters & Returns: request, view. Returns boolean.
# ------------------------------------------------------------------------------
class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Roles.ADMIN)

