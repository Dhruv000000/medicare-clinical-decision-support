# ==============================================================================
# FILE: backend/core/permissions.py
# PURPOSE: Role-based access control (RBAC) and clinical relationship authorization boundaries.
# VIVA EXPLANATION: Implements HIPAA-compliant access control and the critical doctor_can_access_patient boundary, ensuring clinicians can only view records of patients with active appointments, notes, or prescriptions.
# ==============================================================================

from rest_framework.permissions import BasePermission


# --- IsAuthenticatedUser ---
# What it does: Verifies that the requesting user possesses a valid JWT token and is active.
# Why it's structured this way: Base security layer for all protected clinical decision support endpoints.
# Parameters & Returns: Returns True if user is authenticated and active, False otherwise.
# ------------------------------------------------------------------------------
class IsAuthenticatedUser(BasePermission):
    """Verifies that the user is authenticated and active."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active)


# --- IsPatient ---
# What it does: Restricts endpoint access strictly to authenticated patient accounts.
# Why it's structured this way: Prevents doctors and administrators from accidental access to patient-only intake forms.
# Parameters & Returns: Returns True if user possesses role == 'patient'.
# ------------------------------------------------------------------------------
class IsPatient(BasePermission):
    """
    Allows access only to authenticated users with the 'patient' application role.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and getattr(request.user, "role", None) == "patient"
        )


# --- IsDoctor ---
# What it does: Restricts endpoint access strictly to licensed physician accounts.
# Why it's structured this way: Enforces role isolation so patients cannot access clinician management panels.
# Parameters & Returns: Returns True if user possesses role == 'doctor'.
# ------------------------------------------------------------------------------
class IsDoctor(BasePermission):
    """
    Allows access only to authenticated users with the 'doctor' application role.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and getattr(request.user, "role", None) == "doctor"
        )


# --- IsAdmin ---
# What it does: Restricts administrative access strictly to role == 'admin' or superusers.
# Why it's structured this way: Protects system audit logs and global clinical metrics from unauthorized access.
# Parameters & Returns: Returns True if user possesses admin privileges.
# ------------------------------------------------------------------------------
class IsAdmin(BasePermission):
    """
    Allows access only to application administrators (role == 'admin').
    Django superuser is permitted as an explicit developer override.
    Per SRS Correction 3, Django 'is_staff' is NOT treated as application admin.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and (
                getattr(request.user, "role", None) == "admin"
                or getattr(request.user, "is_superuser", False)
            )
        )


# --- IsPatientOwner ---
# What it does: Object-level permission verifying that a clinical record belongs to the requesting patient.
# Why it's structured this way: Prevents IDOR (Insecure Direct Object Reference) data leakage across patients.
# Parameters & Returns: Returns True if the object's patient/user foreign key matches request.user.
# ------------------------------------------------------------------------------
class IsPatientOwner(BasePermission):
    """
    Object-level permission ensuring that patient records are strictly accessed
    only by the owning patient.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Admin override
        if getattr(user, "role", None) == "admin" or getattr(user, "is_superuser", False):
            return True

        target_user = getattr(obj, "patient", None) or getattr(obj, "user", None)
        return target_user == user


# --- doctor_can_access_patient ---
# What it does: Centralized authorization rule verifying active clinical relationship between doctor and patient.
# Why it's structured this way: Enforces HIPAA minimum necessary standard—doctors can only view a patient's data if they have a scheduled/confirmed appointment, clinical notes, or active prescription.
# Parameters & Returns: Takes (doctor_user, patient_user); returns True if authorization exists, False otherwise.
# ------------------------------------------------------------------------------
def doctor_can_access_patient(doctor_user, patient_user):
    """
    Centralized authorization rule for Doctor-Patient access (Correction 4).
    Enforces that a doctor can only access a patient's information if:
      1. Doctor has a scheduled, confirmed, or completed appointment with the patient, OR
      2. Doctor has created clinical observations/notes for the patient, OR
      3. Doctor has prescribed medication for the patient.
    Centralized so Part 2 (reports, predictions, AI) reuses the exact same authority boundary.
    """
    if not doctor_user or not doctor_user.is_authenticated:
        return False
    if getattr(doctor_user, "role", None) != "doctor":
        return False
    if not patient_user:
        return False

    # Avoid circular imports by importing models lazily
    from apps.appointments.models import Appointment
    from apps.doctors.models import ClinicalNote
    from apps.medicines.models import Medication

    has_appointment = Appointment.objects.filter(
        doctor=doctor_user,
        patient=patient_user,
        status__in=["scheduled", "confirmed", "completed"],
    ).exists()

    if has_appointment:
        return True

    has_note = ClinicalNote.objects.filter(
        doctor=doctor_user,
        patient=patient_user,
    ).exists()

    if has_note:
        return True

    has_prescription = Medication.objects.filter(
        prescribed_by=doctor_user,
        patient=patient_user,
    ).exists()

    return has_prescription
