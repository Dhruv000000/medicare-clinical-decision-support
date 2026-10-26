# ==============================================================================
# FILE: backend/apps/doctors/services.py
# PURPOSE: Business logic and access control querying for clinician patient authorization and dashboard metrics.
# VIVA EXPLANATION: Implements the clinical authorization resolver (aggregating patient relationships across appointments, notes, and prescriptions) and aggregates real-time practice KPI metrics from the PostgreSQL database.
# ==============================================================================

from django.utils import timezone
from apps.accounts.models import User
from apps.appointments.models import Appointment
from .models import ClinicalNote


# --- get_authorized_patients_for_doctor ---
# What it does: Computes the mathematical union of patient IDs linked to this doctor via appointments, clinical notes, or prescriptions.
# Why it's structured this way: Enforces HIPAA/GDPR clinical relationship boundaries: a physician cannot view a patient chart without a verifiable clinical event.
# Parameters & Returns: doctor_user (User instance) -> Django QuerySet of Patient User objects with preloaded profiles.
# ------------------------------------------------------------------------------
def get_authorized_patients_for_doctor(doctor_user):
    appointment_patient_ids = Appointment.objects.filter(
        doctor=doctor_user
    ).values_list("patient_id", flat=True)

    note_patient_ids = ClinicalNote.objects.filter(
        doctor=doctor_user
    ).values_list("patient_id", flat=True)

    from apps.medicines.models import Medication
    med_patient_ids = Medication.objects.filter(
        prescribed_by=doctor_user
    ).values_list("patient_id", flat=True)

    all_patient_ids = set(appointment_patient_ids) | set(note_patient_ids) | set(med_patient_ids)

    return User.objects.filter(
        id__in=all_patient_ids,
        role=User.Roles.PATIENT,
    ).select_related("patient_profile").order_by("first_name", "last_name")


# --- get_doctor_insights ---
# What it does: Computes quantitative practice KPIs including today's visits, completed consultations, notes taken, and unique patient volume.
# Why it's structured this way: Replaces hardcoded mock dashboard figures with live aggregated database queries.
# Parameters & Returns: doctor_user (User instance) -> Dict containing KPI metrics.
# ------------------------------------------------------------------------------
def get_doctor_insights(doctor_user):
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    doctor_appointments = Appointment.objects.filter(doctor=doctor_user)
    today_appointments_count = doctor_appointments.filter(
        starts_at__range=(today_start, today_end)
    ).count()

    completed_appointments_count = doctor_appointments.filter(
        status=Appointment.Status.COMPLETED
    ).count()

    total_patients_count = get_authorized_patients_for_doctor(doctor_user).count()
    notes_count = ClinicalNote.objects.filter(doctor=doctor_user).count()

    return {
        "total_patients": total_patients_count,
        "today_appointments_count": today_appointments_count,
        "completed_appointments_count": completed_appointments_count,
        "total_appointments_count": doctor_appointments.count(),
        "clinical_notes_recorded": notes_count,
    }

