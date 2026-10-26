# ==============================================================================
# FILE: backend/apps/medicines/views.py
# PURPOSE: HTTP REST API controllers for prescription tracking, OpenFDA reactions, and drug-drug interactions.
# VIVA EXPLANATION: Exposes medication management and clinical safety APIs. Doctors can prescribe medications for authorized patients, query OpenFDA for real-world adverse event counts and black-box warnings, and perform multi-drug interaction safety checks across active prescriptions.
# ==============================================================================

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError

from core.permissions import IsAuthenticatedUser, doctor_can_access_patient
from core.pagination import StandardResultsSetPagination
from apps.accounts.models import User
from .models import Medication
from .serializers import MedicationSerializer


# --- MedicationListCreateView ---
# What it does: GET lists medications for patient or authorized clinician; POST creates new prescription.
# Why it's structured this way: Enforces role boundaries: doctors can prescribe only for patients with active clinical appointments.
# Parameters & Returns: GET/POST request -> Paginated list or created Medication model.
# ------------------------------------------------------------------------------
class MedicationListCreateView(APIView):
    """
    GET /api/v1/medicines/  — Lists medications for authenticated patient or doctor.
    POST /api/v1/medicines/ — Creates a new prescription or self-reported medication.
    """
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        user = request.user
        queryset = Medication.objects.select_related("patient", "prescribed_by")

        if user.role == User.Roles.PATIENT:
            queryset = queryset.filter(patient=user)
        elif user.role == User.Roles.DOCTOR:
            patient_id = request.query_params.get("patient_id")
            if not patient_id:
                raise ValidationError("Query param 'patient_id' is required for doctors.")
            try:
                patient = User.objects.get(id=patient_id, role=User.Roles.PATIENT)
            except User.DoesNotExist:
                raise NotFound("Patient not found.")
            if not doctor_can_access_patient(user, patient):
                raise PermissionDenied("Unauthorized to view this patient's medications.")
            queryset = queryset.filter(patient=patient)
        elif user.role == User.Roles.ADMIN or user.is_superuser:
            pass
        else:
            raise PermissionDenied("Access denied.")

        active_filter = request.query_params.get("is_active")
        if active_filter is not None:
            queryset = queryset.filter(is_active=active_filter.lower() == "true")

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = MedicationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        user = request.user
        data = request.data.copy()

        if user.role == User.Roles.PATIENT:
            target_patient = user
            prescriber = None
        elif user.role == User.Roles.DOCTOR:
            patient_id = data.get("patient_id")
            if not patient_id:
                raise ValidationError("Field 'patient_id' is required.")
            try:
                target_patient = User.objects.get(id=patient_id, role=User.Roles.PATIENT)
            except User.DoesNotExist:
                raise NotFound("Patient not found.")
            if not doctor_can_access_patient(user, target_patient):
                raise PermissionDenied("Doctor does not have active clinical authorization for this patient.")
            prescriber = user
        else:
            raise PermissionDenied("Only patients or doctors can add medications.")

        serializer = MedicationSerializer(data=data, context={"request": request, "target_patient": target_patient})
        serializer.is_valid(raise_exception=True)

        medication = Medication.objects.create(
            patient=target_patient,
            prescribed_by=prescriber,
            name=serializer.validated_data["name"],
            dosage=serializer.validated_data.get("dosage", ""),
            frequency=serializer.validated_data.get("frequency", ""),
            start_date=serializer.validated_data.get("start_date"),
            end_date=serializer.validated_data.get("end_date"),
            is_active=serializer.validated_data.get("is_active", True),
            notes=serializer.validated_data.get("notes", ""),
        )

        return Response(MedicationSerializer(medication).data, status=status.HTTP_201_CREATED)


# --- MedicationDetailView ---
# What it does: Retrieves single prescription details or updates active status (discontinued / completed).
# Why it's structured this way: Enforces patient and prescriber authorization checks on individual medical records.
# Parameters & Returns: GET/PATCH request with medication_id -> Medication payload.
# ------------------------------------------------------------------------------
class MedicationDetailView(APIView):
    """
    GET /api/v1/medicines/<id>/   — Retrieves single medication details.
    PATCH /api/v1/medicines/<id>/ — Updates medication (e.g. mark inactive / completed).
    """
    permission_classes = [IsAuthenticatedUser]

    def get(self, request, medication_id):
        try:
            medication = Medication.objects.select_related("patient", "prescribed_by").get(id=medication_id)
        except Medication.DoesNotExist:
            raise NotFound(f"Medication with ID {medication_id} not found.")

        user = request.user
        if user.role == User.Roles.PATIENT and medication.patient != user:
            raise PermissionDenied("Unauthorized to access another patient's medication.")
        elif user.role == User.Roles.DOCTOR and not doctor_can_access_patient(user, medication.patient):
            raise PermissionDenied("Unauthorized to access this medication.")

        return Response(MedicationSerializer(medication).data, status=status.HTTP_200_OK)

    def patch(self, request, medication_id):
        try:
            medication = Medication.objects.select_related("patient").get(id=medication_id)
        except Medication.DoesNotExist:
            raise NotFound(f"Medication with ID {medication_id} not found.")

        user = request.user
        if user.role == User.Roles.PATIENT and medication.patient != user:
            raise PermissionDenied("Unauthorized.")
        elif user.role == User.Roles.DOCTOR and not doctor_can_access_patient(user, medication.patient):
            raise PermissionDenied("Unauthorized.")

        serializer = MedicationSerializer(medication, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


# --- OpenFDAReactionsView ---
# What it does: Queries FDA openFDA API to fetch real reported adverse drug reactions and official boxed warnings.
# Why it's structured this way: Caches results 24 hours to reduce external API dependency and protect client response times.
# Parameters & Returns: GET request with drug name -> Adverse reactions, event counts, and boxed warnings.
# ------------------------------------------------------------------------------
class OpenFDAReactionsView(APIView):
    """
    GET /api/v1/medicines/openfda/reactions/?drug=<name>

    Purpose:
        Retrieves real adverse drug reactions and FDA boxed warnings from OpenFDA.
    """
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        drug_name = request.query_params.get("drug", "").strip()
        if not drug_name:
            raise ValidationError("Query parameter 'drug' is required.")

        limit_param = request.query_params.get("limit", "5")
        try:
            limit = max(1, min(20, int(limit_param)))
        except ValueError:
            limit = 5

        from .services.openfda_service import openfda_service

        reactions_data = openfda_service.get_adverse_reactions(drug_name, limit=limit)
        warnings_data = openfda_service.get_boxed_warnings_and_precautions(drug_name)

        return Response(
            {
                "drug": drug_name,
                "adverse_reactions": reactions_data.get("adverse_reactions", []),
                "total_reactions": reactions_data.get("total_reactions_reported", 0),
                "has_boxed_warning": warnings_data.get("has_boxed_warning", False),
                "boxed_warnings": warnings_data.get("boxed_warnings", []),
                "precautions": warnings_data.get("precautions", []),
                "status": reactions_data.get("status", "success"),
                "cached": reactions_data.get("cached", False) or warnings_data.get("cached", False),
            },
            status=status.HTTP_200_OK,
        )


# --- OpenFDAInteractionsView ---
# What it does: Evaluates pairwise drug-drug interactions directly from manufacturer FDA labels.
# Why it's structured this way: Allows rapid screening of arbitrary multi-drug arrays without requiring database medication IDs.
# Parameters & Returns: POST request with list of drug names -> Pairwise interactions report.
# ------------------------------------------------------------------------------
class OpenFDAInteractionsView(APIView):
    """
    POST /api/v1/medicines/openfda/interactions/
    Evaluates pairwise drug-drug interactions for a supplied list of medications.
    """
    permission_classes = [IsAuthenticatedUser]

    def post(self, request):
        drugs = request.data.get("drugs")
        if not drugs or not isinstance(drugs, list):
            raise ValidationError("Field 'drugs' must be a non-empty list of drug names.")

        from .services.openfda_service import openfda_service

        interactions_data = openfda_service.check_interactions(drugs)
        return Response(interactions_data, status=status.HTTP_200_OK)


# --- MedicineInteractionView ---
# What it does: Primary clinical drug safety evaluation endpoint checking candidate drugs against active patient prescriptions.
# Why it's structured this way: Combines OpenFDA and DrugBank intelligence with patient medical records to prevent polypharmacy adverse events.
# Parameters & Returns: POST request -> Interaction risk level, contraindicated pairs, and recommendations.
# ------------------------------------------------------------------------------
class MedicineInteractionView(APIView):
    """
    POST /api/v1/medicines/interactions/

    Purpose:
        Unified medicine interaction analysis endpoint supporting:
        1. Explicit list of medication names: {"drugs": ["warfarin", "aspirin"]}
        2. Single queried drug evaluated against patient's active prescriptions:
           {"queried_drug": "aspirin", "patient_id": 123}
        3. Custom current medications list:
           {"queried_drug": "aspirin", "current_medications": ["warfarin"]}

    Viva Walkthrough:
        - Resolves target patient and enforces doctor-patient authorization boundaries.
        - Invokes interaction_service.evaluate_interactions.
        - Records regulatory audit log entry.
    """
    permission_classes = [IsAuthenticatedUser]

    def post(self, request):
        data = request.data
        user = request.user
        drugs = data.get("drugs")
        queried_drug = data.get("queried_drug")
        current_medications = data.get("current_medications")
        patient_id = data.get("patient_id")

        target_patient = None
        if patient_id:
            try:
                target_patient = User.objects.get(id=patient_id, role=User.Roles.PATIENT)
            except User.DoesNotExist:
                raise NotFound("Patient not found.")

            if user.role == User.Roles.PATIENT and target_patient != user:
                raise PermissionDenied("Patients cannot access another patient's medication records.")
            elif user.role == User.Roles.DOCTOR and not doctor_can_access_patient(user, target_patient):
                raise PermissionDenied("Doctor does not have active clinical authorization for this patient.")
        elif user.role == User.Roles.PATIENT and queried_drug and not drugs:
            target_patient = user

        if not drugs and not queried_drug:
            raise ValidationError("Either 'drugs' (list) or 'queried_drug' (string) must be supplied.")

        from .services.interaction_service import interaction_service
        result = interaction_service.evaluate_interactions(
            drugs=drugs,
            queried_drug=queried_drug,
            patient_user=target_patient,
            current_medications=current_medications,
        )

        if target_patient:
            from apps.audit_logs.services import log_audit_event
            from apps.audit_logs.models import AuditLog
            log_audit_event(
                user=user,
                action=AuditLog.Actions.RECORD_UPDATE,
                resource_type="MedicationInteractions",
                resource_id=target_patient.id,
                request=request,
                metadata={
                    "patient_id": target_patient.id,
                    "drugs_count": len(result.get("drugs_analyzed", [])),
                    "interactions_count": result.get("total_interactions", 0),
                },
            )

        return Response(result, status=status.HTTP_200_OK)
