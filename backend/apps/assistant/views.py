# ==============================================================================
# FILE: backend/apps/assistant/views.py
# PURPOSE: HTTP REST API controllers for the evidence-grounded AI Clinical Assistant.
# VIVA EXPLANATION: Exposes chat and history endpoints for the RAG Clinical Assistant. It authenticates sessions, validates inquiry prompts, ensures HIPAA boundary separation between patient records, and delegates evidence synthesis to the RAG engine.
# ==============================================================================

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError

from core.permissions import IsAuthenticatedUser, doctor_can_access_patient
from core.pagination import StandardResultsSetPagination
from apps.accounts.models import User
from .models import ChatConversation, ChatMessage
from .serializers import ChatConversationSerializer, ChatMessageSerializer
from .services.rag_engine import rag_assistant_engine

logger = logging.getLogger(__name__)


# --- AssistantChatView ---
# What it does: Ingests patient clinical queries and returns evidence-grounded responses citing PubMed research PMIDs.
# Why it's structured this way: Enforces patient privacy rules and session isolation before invoking the RAG pipeline.
# Parameters & Returns: POST request with prompt, conversation_id -> Synthesized clinical response with citations.
# ------------------------------------------------------------------------------
class AssistantChatView(APIView):
    """
    POST /api/v1/assistant/chat/

    Purpose:
        Accepts patient or clinician clinical inquiry, retrieves peer-reviewed
        PubMed citations, assembles patient medical context, and generates
        evidence-based responses.

    Viva / Review Walkthrough:
        - STEP 1: Validate input prompt non-emptiness.
        - STEP 2: Enforce patient data privacy and doctor authorization boundaries.
        - STEP 3: Verify conversation session ownership.
        - STEP 4: Delegate to RAGAssistantEngine for literature grounding and synthesis.
        - STEP 5: Return HTTP 200 with citations and mandatory regulatory disclaimer.
    """
    permission_classes = [IsAuthenticatedUser]

    def post(self, request):
        prompt = request.data.get("prompt", "").strip()
        if not prompt:
            raise ValidationError("Field 'prompt' cannot be empty.")
        if len(prompt) > 4000:
            raise ValidationError("Field 'prompt' exceeds maximum limit of 4000 characters. Please provide a more concise symptom description.")

        conversation_id = request.data.get("conversation_id")
        patient_id = request.data.get("patient_id")
        patient_user = None

        # ----------------------------------------------------------------------
        # STEP 1: RESOLVE PATIENT CONTEXT & ENFORCE AUTHORIZATION
        # ----------------------------------------------------------------------
        if patient_id:
            try:
                target_patient = User.objects.get(id=patient_id, role=User.Roles.PATIENT)
            except User.DoesNotExist:
                raise NotFound("Target patient does not exist.")

            if request.user.role == User.Roles.PATIENT and target_patient != request.user:
                raise PermissionDenied("Patients cannot access another patient's clinical context.")
            elif request.user.role == User.Roles.DOCTOR and not doctor_can_access_patient(request.user, target_patient):
                raise PermissionDenied("Doctor does not have active clinical authorization for this patient.")

            patient_user = target_patient
        elif request.user.role == User.Roles.PATIENT:
            patient_user = request.user

        # ----------------------------------------------------------------------
        # STEP 2: VERIFY CONVERSATION OWNERSHIP
        # ----------------------------------------------------------------------
        if conversation_id:
            existing = ChatConversation.objects.filter(id=conversation_id).first()
            if not existing:
                raise NotFound(f"Conversation with ID {conversation_id} not found.")
            if existing.user != request.user:
                raise PermissionDenied("You cannot access another user's chat conversation.")

        # ----------------------------------------------------------------------
        # STEP 3: EXTRACT PREDICTION CONTEXT & EXECUTE RAG ASSISTANT SERVICE
        # ----------------------------------------------------------------------
        user_symptoms_text = request.data.get("user_symptoms_text")
        top_predicted_disease = request.data.get("top_predicted_disease") or request.data.get("predicted_condition")
        confidence = request.data.get("confidence")
        shap_drivers = request.data.get("shap_drivers") or request.data.get("shap_features")
        prediction_id = request.data.get("prediction_id")
        prediction_context = request.data.get("prediction_context")

        emergency = rag_assistant_engine.detect_emergency(prompt)
        if emergency:
            logger.warning(
                "Red-flag emergency detected in chat query from user %s: categories=%s",
                request.user.id,
                emergency.get("categories"),
            )

        try:
            result = rag_assistant_engine.process_chat(
                user=request.user,
                prompt=prompt,
                patient_user=patient_user,
                conversation_id=conversation_id,
                user_symptoms_text=user_symptoms_text,
                top_predicted_disease=top_predicted_disease,
                confidence=confidence,
                shap_drivers=shap_drivers,
                prediction_id=prediction_id,
                prediction_context=prediction_context,
            )
            return Response(result, status=status.HTTP_200_OK)
        except (ValueError, RuntimeError) as exc:
            logger.error("Clinical Assistant LLM error: %s", exc)
            return Response(
                {
                    "error": {
                        "code": "LLM_PROVIDER_ERROR",
                        "message": str(exc),
                    }
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )


# --- AssistantHistoryView ---
# What it does: Returns paginated multi-turn consultation conversation histories for the logged-in user.
# Why it's structured this way: Uses prefetch_related('messages') to optimize database queries for rapid thread history rendering.
# Parameters & Returns: GET request -> Paginated list of ChatConversation objects with messages and citation sources.
# ------------------------------------------------------------------------------
class AssistantHistoryView(APIView):
    """
    GET /api/v1/assistant/history/

    Purpose:
        Retrieves paginated historical chat conversation threads and source
        literature citations for the authenticated user.
    """
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        conversations = (
            ChatConversation.objects.filter(user=request.user)
            .prefetch_related("messages")
            .order_by("-updated_at")
        )
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(conversations, request)
        serializer = ChatConversationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
