# ==============================================================================
# FILE: backend/tests/test_conversation_pipeline.py
# PURPOSE: Regression test suite for AI chatbot multi-turn conversation handling,
#          dynamic disease prediction pipeline, and confidence representation.
# ==============================================================================

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.core.cache import cache

from apps.accounts.models import User
from apps.assistant.models import ChatConversation, ChatMessage
from apps.assistant.services.rag_engine import rag_assistant_engine
from apps.assistant.services.llm_provider import format_confidence_pct


@pytest.mark.django_db
class TestConversationPipelineRegression:
    """
    Regression test suite ensuring that:
    1. Each user message with symptoms triggers a fresh prediction using current symptoms.
    2. Conversational history is preserved strictly as dialogue context without stale prediction hijacking.
    3. Model outputs (probabilities in [0.0, 1.0]) are properly formatted as percentages (e.g., '85.3%', never '0.8527%').
    4. Literature references are validated for relevance to the predicted disease.
    5. Neither result is presented as a confirmed diagnosis (qualified impression with differentials).
    """

    @pytest.fixture(autouse=True)
    def setup_data(self):
        cache.clear()
        self.patient_user = User.objects.create_user(
            email="patient.regression@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
            first_name="Jane",
            last_name="Doe",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.patient_user)

    def test_confidence_representation_formatting(self):
        """
        Verify that model outputs (probabilities, logits, or percentage strings)
        are cleanly formatted as percentage strings and never as '0.8527%'.
        """
        assert format_confidence_pct(0.8527) == "85.3"
        assert format_confidence_pct(0.7367) == "73.7"
        assert format_confidence_pct("0.8527") == "85.3"
        assert format_confidence_pct("85.3%") == "85.3"
        assert format_confidence_pct(85.3) == "85.3"
        assert format_confidence_pct(1.0) == "100.0"
        assert format_confidence_pct(0.0) == "0.0"
        assert format_confidence_pct(None, default=75.0) == "75.0"

    def test_sequential_multi_turn_disease_prediction_service(self):
        """
        Service-level regression test:
        Turn 1: Leptospirosis symptoms -> Leptospirosis impression.
        Turn 2: Allergic Rhinitis symptoms in the same conversation -> Allergic Rhinitis impression.
        Verify Turn 2 does NOT repeat Turn 1's diagnosis or stale confidence.
        """
        turn1_prompt = (
            "sudden fever, severe calf muscle pain, headache, red eyes, "
            "recent floodwater exposure, weakness, and nausea"
        )
        r1 = rag_assistant_engine.process_chat(
            user=self.patient_user,
            prompt=turn1_prompt,
        )

        conv_id = r1["conversation_id"]
        assert conv_id is not None
        assert "Leptospirosis" in r1["predicted_condition"]
        assert 0.0 < float(r1["confidence"]) <= 1.0
        # Check that response formats confidence as a percentage (e.g. 73.7%), NOT 0.7367%
        assert "0.7367%" not in r1["response"]
        assert "0.8527%" not in r1["response"]
        assert "%" in r1["response"]
        # Ensure framed as clinical impression, not confirmed diagnosis
        assert "initial clinical impression" in r1["response"].lower() or "impression" in r1["response"].lower()
        assert "not a confirmed" in r1["response"].lower() or "does not constitute" in r1["response"].lower()

        # Check citations relevance for Leptospirosis
        assert len(r1["citations"]) > 0
        citation_texts = " ".join([c.get("title", "") + " " + c.get("journal", "") for c in r1["citations"]]).lower()
        assert "leptospir" in citation_texts or "infect" in citation_texts

        # Turn 2: Distinct allergic rhinitis symptoms in the EXACT same conversation
        turn2_prompt = (
            "repeated sneezing, itchy nose, clear watery nasal discharge, "
            "itchy watery eyes, and dust/pollen triggers"
        )
        r2 = rag_assistant_engine.process_chat(
            user=self.patient_user,
            prompt=turn2_prompt,
            conversation_id=conv_id,
        )

        assert r2["conversation_id"] == conv_id
        # Turn 2 must independently assess Allergic Rhinitis, NOT repeat Leptospirosis
        assert "Allergic Rhinitis" in r2["predicted_condition"]
        assert "Leptospirosis" not in r2["predicted_condition"]
        assert 0.0 < float(r2["confidence"]) <= 1.0
        assert "0.9454%" not in r2["response"]
        assert "%" in r2["response"]

        # Ensure Turn 2 citations are relevant to Allergic Rhinitis / Rhinitis
        assert len(r2["citations"]) > 0
        r2_citation_texts = " ".join([c.get("title", "") + " " + c.get("journal", "") for c in r2["citations"]]).lower()
        assert "rhinitis" in r2_citation_texts or "allerg" in r2_citation_texts or "nasal" in r2_citation_texts

        # Check that both turns are recorded in the conversation
        conversation = ChatConversation.objects.get(id=conv_id)
        messages = list(conversation.messages.order_by("created_at"))
        assert len(messages) == 4  # [user1, assistant1, user2, assistant2]
        assert messages[0].content == turn1_prompt
        assert messages[2].content == turn2_prompt

    def test_sequential_multi_turn_via_api_endpoint(self):
        """
        API-level regression test:
        POST /api/v1/assistant/chat/ sequentially with two different symptom descriptions.
        Verify full request-response lifecycle from HTTP layer down to LLM provider.
        """
        # Turn 1: Leptospirosis
        turn1_payload = {
            "prompt": "sudden fever, severe calf muscle pain, headache, red eyes, recent floodwater exposure, weakness, and nausea",
        }
        res1 = self.client.post("/api/v1/assistant/chat/", data=turn1_payload, format="json")
        assert res1.status_code == status.HTTP_200_OK
        data1 = res1.json()

        conv_id = data1["conversation_id"]
        assert conv_id is not None
        assert "Leptospirosis" in data1["predicted_condition"]
        assert "0.8527%" not in data1["response"]
        assert "initial clinical impression" in data1["response"].lower() or "impression" in data1["response"].lower()

        # Turn 2: Allergic Rhinitis in same conversation
        turn2_payload = {
            "prompt": "repeated sneezing, itchy nose, clear watery nasal discharge, itchy watery eyes, and dust/pollen triggers",
            "conversation_id": conv_id,
        }
        res2 = self.client.post("/api/v1/assistant/chat/", data=turn2_payload, format="json")
        assert res2.status_code == status.HTTP_200_OK
        data2 = res2.json()

        assert data2["conversation_id"] == conv_id
        assert "Allergic Rhinitis" in data2["predicted_condition"]
        assert "Leptospirosis" not in data2["predicted_condition"]
        assert "0.9454%" not in data2["response"]
        assert "0.8527%" not in data2["response"]

        # Literature citations must match Allergic Rhinitis
        assert len(data2["citations"]) > 0
        c_titles = [c["title"].lower() for c in data2["citations"]]
        assert any("rhinitis" in t or "allerg" in t or "nasal" in t for t in c_titles)

    def test_conversation_context_preserved_for_non_symptom_followup(self):
        """
        Verify that when a user asks a follow-up inquiry without new symptoms,
        the chatbot provides helpful guidance and does not hallucinate a fake condition.
        """
        turn1_payload = {
            "prompt": "repeated sneezing, itchy nose, clear watery nasal discharge, itchy watery eyes, and dust/pollen triggers",
        }
        res1 = self.client.post("/api/v1/assistant/chat/", data=turn1_payload, format="json")
        assert res1.status_code == status.HTTP_200_OK
        conv_id = res1.json()["conversation_id"]

        # Follow-up question without symptoms
        followup_payload = {
            "prompt": "What non-pharmacological lifestyle steps can help reduce dust allergen exposure at home?",
            "conversation_id": conv_id,
        }
        res2 = self.client.post("/api/v1/assistant/chat/", data=followup_payload, format="json")
        assert res2.status_code == status.HTTP_200_OK
        data2 = res2.json()
        assert data2["conversation_id"] == conv_id
        # Should not falsely report high-confidence acute condition
        assert data2.get("confidence") is None or float(data2.get("confidence", 0)) < 0.5
