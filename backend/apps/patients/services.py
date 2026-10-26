# ==============================================================================
# FILE: backend/apps/patients/services.py
# PURPOSE: Service layer aggregating live database metrics for patient dashboard telemetry.
# VIVA EXPLANATION: Gathers dynamic operational metrics across appointments, active prescriptions, electronic medical records, lab reports, and machine learning disease predictions without resorting to mock figures.
# ==============================================================================

from django.utils import timezone


# --- get_patient_dashboard_data ---
# What it does: Queries and summarizes patient clinical activity into a single JSON KPI payload.
# Why it's structured this way: Uses local imports to prevent circular dependency cycles between apps and batches queries for high responsiveness.
# Parameters & Returns: patient_user (User instance) -> Dict containing counts and next appointment metadata.
# ------------------------------------------------------------------------------
def get_patient_dashboard_data(patient_user):
    from apps.appointments.models import Appointment
    from apps.medical_records.models import MedicalRecord, LabReport
    from apps.medicines.models import Medication
    from apps.predictions.models import DiseasePrediction

    now = timezone.now()

    upcoming_appointments = (
        Appointment.objects.filter(
            patient=patient_user,
            status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED],
            starts_at__gte=now,
        )
        .select_related("doctor")
        .order_by("starts_at")
    )

    next_apt = upcoming_appointments.first()
    next_apt_data = None
    if next_apt:
        next_apt_data = {
            "id": next_apt.id,
            "doctor_name": f"{next_apt.doctor.first_name} {next_apt.doctor.last_name}".strip() or next_apt.doctor.email,
            "starts_at": next_apt.starts_at,
            "reason": next_apt.reason,
            "status": next_apt.status,
        }

    active_medications_count = Medication.objects.filter(
        patient=patient_user,
        is_active=True,
    ).count()

    total_records_count = MedicalRecord.objects.filter(patient=patient_user).count()
    total_reports_count = LabReport.objects.filter(patient=patient_user).count()
    total_predictions_count = DiseasePrediction.objects.filter(patient=patient_user).count()

    return {
        "upcoming_appointments_count": upcoming_appointments.count(),
        "next_appointment": next_apt_data,
        "active_medications_count": active_medications_count,
        "medical_records_count": total_records_count,
        "lab_reports_count": total_reports_count,
        "past_predictions_count": total_predictions_count,
    }

