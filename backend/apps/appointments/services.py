# ==============================================================================
# FILE: backend/apps/appointments/services.py
# PURPOSE: Business logic service for appointment creation, status lifecycle transitions, and audit logging.
# VIVA EXPLANATION: Encapsulates appointment booking and modification logic, emitting HIPAA audit events for every schedule change and state transition.
# ==============================================================================

from apps.accounts.models import User
from apps.audit_logs.services import log_audit_event
from apps.audit_logs.models import AuditLog
from .models import Appointment


# --- create_appointment ---
# What it does: Creates an Appointment instance with SCHEDULED status and records an APPOINTMENT_CREATE audit event.
# Why it's structured this way: Decouples model persistence and audit logging from the DRF view.
# Parameters & Returns: Takes patient_user, doctor_id, starts_at, reason, notes, request; returns Appointment.
# ------------------------------------------------------------------------------
def create_appointment(patient_user, doctor_id, starts_at, reason="", notes="", request=None):
    doctor = User.objects.get(id=doctor_id, role=User.Roles.DOCTOR)
    appointment = Appointment.objects.create(
        patient=patient_user,
        doctor=doctor,
        starts_at=starts_at,
        reason=reason,
        notes=notes,
        status=Appointment.Status.SCHEDULED,
    )
    log_audit_event(
        user=patient_user,
        action=AuditLog.Actions.APPOINTMENT_CREATE,
        resource_type="Appointment",
        resource_id=appointment.id,
        request=request,
        metadata={"doctor_id": doctor.id, "starts_at": starts_at.isoformat()},
    )
    return appointment


# --- update_appointment ---
# What it does: Updates appointment fields (such as status transitions) and logs the state change in the AuditLog.
# Why it's structured this way: Captures before-and-after status tracking (e.g. 'scheduled -> confirmed') for clinical review.
# Parameters & Returns: Takes appointment, validated_data, acting_user, request; returns updated Appointment.
# ------------------------------------------------------------------------------
def update_appointment(appointment, validated_data, acting_user, request=None):
    old_status = appointment.status
    for attr, val in validated_data.items():
        setattr(appointment, attr, val)
    appointment.save()

    metadata = {"status_changed": f"{old_status} -> {appointment.status}"}
    log_audit_event(
        user=acting_user,
        action=AuditLog.Actions.APPOINTMENT_UPDATE,
        resource_type="Appointment",
        resource_id=appointment.id,
        request=request,
        metadata=metadata,
    )
    return appointment
