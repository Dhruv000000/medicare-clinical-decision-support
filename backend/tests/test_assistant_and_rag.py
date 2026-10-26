import pytest
from unittest.mock import patch, MagicMock
import requests
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User
from apps.doctors.models import DoctorProfile
from apps.patients.models import PatientProfile
from apps.appointments.models import Appointment
from apps.assistant.models import ChatConversation, ChatMessage
from apps.assistant.services.pubmed_service import pubmed_service
from apps.assistant.services.rag_engine import rag_assistant_engine, MANDATORY_REGULATORY_DISCLAIMER


@pytest.mark.django_db
class TestAssistantAndPubMedRAG:
    """
    Test suite for PubMed E-utilities integration, RAG clinical engine,
    authorization boundaries, conversation persistence, and REST endpoints.
    """

    @pytest.fixture(autouse=True)
    def setup_data(self):
        cache.clear()

        # Doctor 1 & profile
        self.doc1_user = User.objects.create_user(
            email="doc1.rag@medicare.local",
            password="Password123!",
            role=User.Roles.DOCTOR,
            first_name="Gregory",
            last_name="House",
        )
        self.doc1_profile = DoctorProfile.objects.create(
            user=self.doc1_user,
            license_number="DOC-RAG-001",
            specialization="Internal Medicine",
        )

        # Doctor 2 & profile
        self.doc2_user = User.objects.create_user(
            email="doc2.rag@medicare.local",
            password="Password123!",
            role=User.Roles.DOCTOR,
            first_name="James",
            last_name="Wilson",
        )
        self.doc2_profile = DoctorProfile.objects.create(
            user=self.doc2_user,
            license_number="DOC-RAG-002",
            specialization="Oncology",
        )

        # Patient 1 & profile
        self.pat1_user = User.objects.create_user(
            email="pat1.rag@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
            first_name="John",
            last_name="Doe",
        )
        self.pat1_profile = PatientProfile.objects.create(
            user=self.pat1_user,
            emergency_contact="1234567890",
        )

        # Patient 2 & profile
        self.pat2_user = User.objects.create_user(
            email="pat2.rag@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
            first_name="Jane",
            last_name="Smith",
        )
        self.pat2_profile = PatientProfile.objects.create(
            user=self.pat2_user,
            emergency_contact="0987654321",
        )

        from django.utils import timezone
        # Active Appointment: Doctor 1 <-> Patient 1
        Appointment.objects.create(
            doctor=self.doc1_user,
            patient=self.pat1_user,
            status=Appointment.Status.CONFIRMED,
            starts_at=timezone.now() + timezone.timedelta(days=1),
        )

        self.client = APIClient()

    # -------------------------------------------------------------------------
    # PubMed Service Tests
    # -------------------------------------------------------------------------

    @patch("requests.get")
    def test_pubmed_service_mocked_success(self, mock_get):
        # Mock ESearch
        esearch_resp = MagicMock()
        esearch_resp.status_code = 200
        esearch_resp.json.return_value = {
            "esearchresult": {"idlist": ["12345678", "87654321"]}
        }

        # Mock ESummary
        esummary_resp = MagicMock()
        esummary_resp.status_code = 200
        esummary_resp.json.return_value = {
            "result": {
                "12345678": {
                    "title": "Clinical Efficacy of Novel Antihypertensive Regimens.",
                    "source": "The Lancet",
                    "pubdate": "2023 Nov",
                    "authors": [{"name": "Smith J"}, {"name": "Brown A"}],
                },
                "87654321": {
                    "title": "Comprehensive Guidelines for Arterial Hypertension.",
                    "source": "New England Journal of Medicine",
                    "pubdate": "2022",
                    "authors": [{"name": "Johnson K"}],
                },
            }
        }

        mock_get.side_effect = [esearch_resp, esummary_resp]

        result = pubmed_service.search_pubmed("hypertension treatment", limit=2)
        assert result["status"] == "success"
        assert len(result["citations"]) == 2
        assert result["citations"][0]["pmid"] == "12345678"
        assert result["citations"][0]["title"] == "Clinical Efficacy of Novel Antihypertensive Regimens"
        assert result["citations"][0]["journal"] == "The Lancet"
        assert result["citations"][0]["year"] == "2023"
        assert result["cached"] is False

    @patch("requests.get")
    def test_pubmed_service_caching_24h(self, mock_get):
        esearch_resp = MagicMock()
        esearch_resp.status_code = 200
        esearch_resp.json.return_value = {"esearchresult": {"idlist": ["11112222"]}}

        esummary_resp = MagicMock()
        esummary_resp.status_code = 200
        esummary_resp.json.return_value = {
            "result": {
                "11112222": {
                    "title": "Study on Metformin.",
                    "source": "Diabetes Care",
                    "pubdate": "2021",
                    "authors": [{"name": "Adams C"}],
                }
            }
        }

        mock_get.side_effect = [esearch_resp, esummary_resp]

        # Call 1: uncached
        res1 = pubmed_service.search_pubmed("metformin diabetes", limit=1)
        assert res1["cached"] is False
        assert mock_get.call_count == 2

        # Call 2: cached
        res2 = pubmed_service.search_pubmed("metformin diabetes", limit=1)
        assert res2["cached"] is True
        assert mock_get.call_count == 2  # No new network requests
        assert res2["citations"] == res1["citations"]

    @patch("requests.get")
    def test_pubmed_service_timeout_fallback(self, mock_get):
        mock_get.side_effect = requests.Timeout("NCBI Entrez service timed out.")

        res = pubmed_service.search_pubmed("hypertension", limit=2)
        assert res["status"] == "fallback"
        assert len(res["citations"]) > 0
        assert "Guideline" in res["citations"][0]["title"]
        assert "29146124" == res["citations"][0]["pmid"]

    # -------------------------------------------------------------------------
    # RAG Assistant Engine Unit Tests
    # -------------------------------------------------------------------------

    def test_rag_engine_synthesizes_disclaimer_and_citations(self):
        result = rag_assistant_engine.process_chat(
            user=self.pat1_user,
            prompt="What are optimal non-pharmacological therapies for hypertension?",
        )

        assert "conversation_id" in result
        assert "message_id" in result
        assert "response" in result
        assert "citations" in result
        assert result["disclaimer"] == MANDATORY_REGULATORY_DISCLAIMER
        assert "hypertension" in result["response"].lower()

        # Check DB persistence
        conv = ChatConversation.objects.get(id=result["conversation_id"])
        assert conv.user == self.pat1_user
        assert conv.messages.count() == 2  # 1 user + 1 assistant

        user_msg = conv.messages.filter(role="user").first()
        assistant_msg = conv.messages.filter(role="assistant").first()
        assert "non-pharmacological therapies" in user_msg.content
        assert len(assistant_msg.sources) > 0

    # -------------------------------------------------------------------------
    # REST API Endpoint Tests (/api/v1/assistant/chat/ & history/)
    # -------------------------------------------------------------------------

    def test_chat_unauthenticated_forbidden(self):
        res = self.client.post("/api/v1/assistant/chat/", {"prompt": "Hello"}, format="json")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_chat_empty_prompt_validation_error(self):
        self.client.force_authenticate(user=self.pat1_user)
        res = self.client.post("/api/v1/assistant/chat/", {"prompt": "  "}, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_patient_can_chat_and_continue_conversation(self):
        self.client.force_authenticate(user=self.pat1_user)

        # Initial turn
        payload1 = {"prompt": "What should I know about managing type 2 diabetes?"}
        res1 = self.client.post("/api/v1/assistant/chat/", payload1, format="json")
        assert res1.status_code == status.HTTP_200_OK
        data1 = res1.json()

        conv_id = data1["conversation_id"]
        assert conv_id is not None
        assert data1["disclaimer"] == MANDATORY_REGULATORY_DISCLAIMER
        assert len(data1["citations"]) > 0

        # Subsequent turn on same conversation
        payload2 = {"prompt": "Can exercise help lower blood sugar?", "conversation_id": conv_id}
        res2 = self.client.post("/api/v1/assistant/chat/", payload2, format="json")
        assert res2.status_code == status.HTTP_200_OK
        data2 = res2.json()

        assert data2["conversation_id"] == conv_id
        # Total messages in this conversation should now be 4 (2 user, 2 assistant)
        conv = ChatConversation.objects.get(id=conv_id)
        assert conv.messages.count() == 4

    def test_unauthorized_user_cannot_access_or_append_to_another_users_conversation(self):
        # Patient 1 creates a conversation
        conv = ChatConversation.objects.create(user=self.pat1_user, title="Private Chat")
        ChatMessage.objects.create(conversation=conv, role="user", content="Secret data")

        # Patient 2 tries to append to Patient 1's conversation
        self.client.force_authenticate(user=self.pat2_user)
        payload = {"prompt": "Hijack attempt", "conversation_id": conv.id}
        res = self.client.post("/api/v1/assistant/chat/", payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_doctor_cannot_query_unauthorized_patient_context(self):
        # Doctor 2 has NO relationship with Patient 1
        self.client.force_authenticate(user=self.doc2_user)
        payload = {
            "prompt": "Evaluate patient's lab results",
            "patient_id": self.pat1_user.id,
        }
        res = self.client.post("/api/v1/assistant/chat/", payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert "authorization" in res.json()["error"]["message"].lower()

    def test_doctor_can_query_authorized_patient_context(self):
        # Doctor 1 has active confirmed appointment with Patient 1
        self.client.force_authenticate(user=self.doc1_user)
        payload = {
            "prompt": "Evaluate patient's blood pressure trajectory",
            "patient_id": self.pat1_user.id,
        }
        res = self.client.post("/api/v1/assistant/chat/", payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["conversation_id"] is not None
        assert data["disclaimer"] == MANDATORY_REGULATORY_DISCLAIMER

    def test_patient_cannot_query_another_patient_context(self):
        # Patient 1 tries to query with Patient 2's id
        self.client.force_authenticate(user=self.pat1_user)
        payload = {
            "prompt": "Tell me about Jane",
            "patient_id": self.pat2_user.id,
        }
        res = self.client.post("/api/v1/assistant/chat/", payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_assistant_history_isolation(self):
        # Patient 1 has 2 conversations
        conv1 = ChatConversation.objects.create(user=self.pat1_user, title="Pat1 Chat 1")
        ChatMessage.objects.create(conversation=conv1, role="user", content="Msg 1")
        conv2 = ChatConversation.objects.create(user=self.pat1_user, title="Pat1 Chat 2")
        ChatMessage.objects.create(conversation=conv2, role="user", content="Msg 2")

        # Patient 2 has 1 conversation
        conv3 = ChatConversation.objects.create(user=self.pat2_user, title="Pat2 Chat 1")
        ChatMessage.objects.create(conversation=conv3, role="user", content="Pat2 Msg")

        # Query Patient 1 history
        self.client.force_authenticate(user=self.pat1_user)
        res1 = self.client.get("/api/v1/assistant/history/")
        assert res1.status_code == status.HTTP_200_OK
        data1 = res1.json()
        assert data1["count"] == 2
        titles = [c["title"] for c in data1["results"]]
        assert "Pat1 Chat 1" in titles
        assert "Pat1 Chat 2" in titles
        assert "Pat2 Chat 1" not in titles

        # Query Patient 2 history
        self.client.force_authenticate(user=self.pat2_user)
        res2 = self.client.get("/api/v1/assistant/history/")
        assert res2.status_code == status.HTTP_200_OK
        data2 = res2.json()
        assert data2["count"] == 1
        assert data2["results"][0]["title"] == "Pat2 Chat 1"

    # -------------------------------------------------------------------------
    # Intent Classification, Biomarker Injection & Query Formulation Tests
    # -------------------------------------------------------------------------

    def test_app_navigation_intent_routes_without_pubmed(self):
        """
        Verifies that questions regarding app navigation (e.g. appointment booking,
        record uploads) are routed to app guidance directly without querying PubMed.
        """
        with patch("apps.assistant.services.pubmed_service.pubmed_service.search_pubmed") as mock_pubmed:
            self.client.force_authenticate(user=self.pat1_user)

            # Test prompt: "from where i can apply for appointement in this app"
            res1 = self.client.post(
                "/api/v1/assistant/chat/",
                {"prompt": "from where i can apply for appointement in this app"},
                format="json",
            )
            assert res1.status_code == status.HTTP_200_OK
            data1 = res1.json()

            assert data1["intent"] == "APP_NAVIGATION"
            assert "Appointments" in data1["response"]
            assert "Book Appointment" in data1["response"]
            assert data1["citations"] == []
            mock_pubmed.assert_not_called()

            # Test upload prompt
            res2 = self.client.post(
                "/api/v1/assistant/chat/",
                {"prompt": "how to upload my lab report records"},
                format="json",
            )
            assert res2.status_code == status.HTTP_200_OK
            data2 = res2.json()
            assert data2["intent"] == "APP_NAVIGATION"
            assert "Lab Tests" in data2["response"] or "Upload Report" in data2["response"]
            assert data2["citations"] == []
            mock_pubmed.assert_not_called()

    def test_lab_explanation_injects_actual_patient_biomarkers(self):
        """
        Verifies that when the user asks to explain lab results, the assistant retrieves
        actual extracted LabResult records from the DB and interprets them dynamically.
        """
        from apps.medical_records.models import LabReport, LabResult

        report = LabReport.objects.create(
            patient=self.pat1_user,
            title="Comprehensive Metabolic Panel",
        )
        LabResult.objects.create(report=report, test_name="Fasting Blood Glucose", value="168", unit="mg/dL", flag="high")
        LabResult.objects.create(report=report, test_name="HbA1c", value="8.4", unit="%", flag="high")
        LabResult.objects.create(report=report, test_name="Serum Creatinine", value="1.38", unit="mg/dL", flag="high")
        LabResult.objects.create(report=report, test_name="Total Cholesterol", value="242", unit="mg/dL", flag="high")
        LabResult.objects.create(report=report, test_name="Triglycerides", value="218", unit="mg/dL", flag="high")
        LabResult.objects.create(report=report, test_name="HDL Cholesterol", value="34", unit="mg/dL", flag="low")
        LabResult.objects.create(report=report, test_name="Platelet Count", value="284000", unit="cells/mcL", flag="normal")

        with patch("apps.assistant.services.pubmed_service.pubmed_service.search_pubmed") as mock_pubmed:
            mock_pubmed.return_value = {
                "status": "success",
                "citations": [
                    {
                        "pmid": "34964812",
                        "title": "Standards of Medical Care in Diabetes-2022",
                        "journal": "Clinical Diabetes",
                        "year": "2022",
                        "abstract": "Hyperglycemia and elevated HbA1c increase cardiovascular and renal complications.",
                    }
                ],
            }

            self.client.force_authenticate(user=self.pat1_user)
            res = self.client.post(
                "/api/v1/assistant/chat/",
                {"prompt": "Explain my latest lab results"},
                format="json",
            )
            assert res.status_code == status.HTTP_200_OK
            data = res.json()

            assert data["intent"] == "LAB_EXPLANATION"
            assert data["patient_context_applied"] is True

            # Verify that PubMed query formulation used extracted clinical keywords rather than raw prompt
            mock_pubmed.assert_called_once()
            called_query = mock_pubmed.call_args[0][0]
            assert "Explain my latest lab results" not in called_query
            assert "hyperglycemia" in called_query or "hba1c" in called_query.lower()

            # Verify the response interprets the specific elevated biomarkers
            resp = data["response"]
            assert "168" in resp or "hyperglycemia" in resp.lower()
            assert "8.4" in resp or "hba1c" in resp.lower()
            assert "1.38" in resp or "creatinine" in resp.lower()
            assert "physician" in resp.lower() or "doctor" in resp.lower() or "endocrinologist" in resp.lower()

    def test_pubmed_empty_results_no_arbitrary_fallback(self):
        """
        Verifies that if a PubMed search returns 0 results, it returns empty citations
        without injecting arbitrary fallback articles.
        """
        with patch("requests.get") as mock_get:
            # Mock empty esearch
            mock_get.status_code = 200
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "esearchresult": {"idlist": [], "count": "0"}
            }

            res = pubmed_service.search_pubmed("rare unindexed medical entity", limit=3)
            assert res["status"] == "no_results"
            assert res["citations"] == []
            assert res["total_results"] == 0

    def test_red_flag_emergency_triage_protocol(self):
        """
        Verifies that acute red-flag emergency symptoms immediately return an emergency alert banner
        directing the user to emergency services, and do NOT invoke PubMed lookups or cite academic papers.
        """
        emergency_prompts = [
            "I have acute pain in heart/chest and left chest pain",
            "Severe shortness of breath, I can't breathe",
            "Sudden numbness in arm with facial drooping and slurred speech",
            "Severe hemorrhage and coughing up blood",
            "Sudden loss of consciousness and passed out",
        ]

        with patch("apps.assistant.services.pubmed_service.pubmed_service.search_pubmed") as mock_pubmed:
            self.client.force_authenticate(user=self.pat1_user)

            for prompt in emergency_prompts:
                mock_pubmed.reset_mock()
                res = self.client.post(
                    "/api/v1/assistant/chat/",
                    {"prompt": prompt},
                    format="json",
                )
                assert res.status_code == status.HTTP_200_OK
                data = res.json()

                assert data["is_emergency"] is True
                assert data["intent"] == "EMERGENCY_TRIAGE"
                assert data["citations"] == []
                mock_pubmed.assert_not_called()
                assert "EMERGENCY" in data["response"]
                assert ("911" in data["response"] or "112" in data["response"] or "108" in data["response"])

    def test_system_prompt_context_not_leaked_and_no_robotic_opening(self):
        """
        Verifies that internal patient clinical context headers and system prompt strings
        are never echoed back to the user-facing response, and robotic template openings are omitted.
        """
        from apps.medical_records.models import LabReport, LabResult

        report = LabReport.objects.create(
            patient=self.pat1_user,
            title="Recent Blood Panel",
        )
        LabResult.objects.create(report=report, test_name="Serum Creatinine", value="1.45", unit="mg/dL", flag="high")

        self.client.force_authenticate(user=self.pat1_user)
        res = self.client.post(
            "/api/v1/assistant/chat/",
            {"prompt": "What are common triggers for migraine?"},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        resp = data["response"]

        # Ensure no system context leaked into output
        assert "Patient Clinical Context:" not in resp
        assert "Patient Profile:" not in resp
        assert "CONFIDENTIAL INTERNAL SYSTEM CONTEXT" not in resp

        # Ensure robotic template opening is not present
        assert "In response to your inquiry regarding" not in resp
        assert len(resp) > 40

    def test_pubmed_keywords_regenerated_dynamically_per_turn(self):
        """
        Verifies that previous abnormal lab results from a prior turn or EHR context do not
        persist into new, unrelated inquiries like asthma or allergies.
        """
        from apps.medical_records.models import LabReport, LabResult

        report = LabReport.objects.create(
            patient=self.pat1_user,
            title="Metabolic Profile",
        )
        LabResult.objects.create(report=report, test_name="Fasting Blood Glucose", value="180", unit="mg/dL", flag="high")
        LabResult.objects.create(report=report, test_name="Serum Creatinine", value="1.50", unit="mg/dL", flag="high")

        with patch("apps.assistant.services.pubmed_service.pubmed_service.search_pubmed") as mock_pubmed:
            mock_pubmed.return_value = {
                "status": "success",
                "citations": [],
            }

            self.client.force_authenticate(user=self.pat1_user)
            # Ask an unrelated medical question
            res = self.client.post(
                "/api/v1/assistant/chat/",
                {"prompt": "What are evidence-based management strategies for asthma?"},
                format="json",
            )
            assert res.status_code == status.HTTP_200_OK

            mock_pubmed.assert_called_once()
            called_query = mock_pubmed.call_args[0][0].lower()

            # The query must be dynamic for asthma, not stuck on diabetes/kidney
            assert "asthma" in called_query
            assert "hyperglycemia" not in called_query
            assert "diabetic nephropathy" not in called_query

    def test_acute_chest_pain_triggers_emergency_triage(self):
        """
        Verifies that acute chest distress triggers ("squeezing pressure on chest",
        "radiating to jaw/arm", "chest pain", "acute chest distress") ALWAYS trigger
        the Red-Flag Emergency Triage Alert without providing routine text responses.
        """
        chest_prompts = [
            "squeezing pressure on chest",
            "radiating to jaw/arm",
            "chest pain",
            "squeezing pressure on chest, radiating to jaw/arm",
            "acute chest distress",
            "left chest pain",
            "I have severe pain radiating to my left arm and jaw",
        ]

        with patch("apps.assistant.services.pubmed_service.pubmed_service.search_pubmed") as mock_pubmed:
            self.client.force_authenticate(user=self.pat1_user)

            for prompt in chest_prompts:
                mock_pubmed.reset_mock()
                res = self.client.post(
                    "/api/v1/assistant/chat/",
                    {"prompt": prompt},
                    format="json",
                )
                assert res.status_code == status.HTTP_200_OK, f"Failed on prompt: {prompt}"
                data = res.json()

                assert data["is_emergency"] is True, f"Expected is_emergency=True for: {prompt}"
                assert data["intent"] == "EMERGENCY_TRIAGE", f"Expected EMERGENCY_TRIAGE for: {prompt}"
                assert data["citations"] == []
                mock_pubmed.assert_not_called()
                assert "EMERGENCY" in data["response"]
                assert ("911" in data["response"] or "112" in data["response"] or "108" in data["response"])
                # Ensure no routine medical advice was given
                assert "Key Findings & Out-of-Range Metrics" not in data["response"]

    def test_general_medical_question_does_not_dump_lab_report(self):
        """
        Verifies that asking a general medical question (e.g. mixed dyslipidemia)
        answers the medical question directly using plain language without dumping
        the patient's full lab report or out-of-range metrics.
        """
        from apps.medical_records.models import LabReport, LabResult

        # Seed abnormal lab results on file for the patient
        report = LabReport.objects.create(
            patient=self.pat1_user,
            title="Comprehensive Metabolic Panel",
        )
        LabResult.objects.create(report=report, test_name="Fasting Blood Glucose", value="185", unit="mg/dL", flag="high")
        LabResult.objects.create(report=report, test_name="Serum Creatinine", value="1.62", unit="mg/dL", flag="high")
        LabResult.objects.create(report=report, test_name="Total Cholesterol", value="248", unit="mg/dL", flag="high")

        self.client.force_authenticate(user=self.pat1_user)
        res = self.client.post(
            "/api/v1/assistant/chat/",
            {"prompt": "What are the first-line treatments for mixed dyslipidemia?"},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.json()

        assert data["intent"] == "MEDICAL_QUESTION"
        resp = data["response"]

        # MUST NOT dump the patient's personal lab report or out-of-range block
        assert "Key Findings & Out-of-Range Metrics" not in resp
        assert "Based on your latest laboratory report records" not in resp
        assert "185 mg/dL" not in resp
        assert "1.62 mg/dL" not in resp
        assert "248 mg/dL" not in resp

        # Must provide direct, plain-language guidance for dyslipidemia
        assert "statin" in resp.lower() or "cholesterol" in resp.lower()
        # Must use layman-friendly language
        assert "atherogenic lipids" not in resp.lower()

    def test_myth_busting_question_directly_refutes_first(self):
        """
        Verifies that myth-busting inquiries (e.g. eating blue chalk to cure blood pressure)
        directly address and refute the myth first, explain pica risks, and provide
        evidence-based guidance without dumping the patient's lab report.
        """
        self.client.force_authenticate(user=self.pat1_user)
        res = self.client.post(
            "/api/v1/assistant/chat/",
            {"prompt": "Can eating blue chalk cure my blood pressure?"},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.json()

        resp = data["response"]

        # Directly refute the myth first
        assert "No, eating chalk does not treat high blood pressure and can be dangerous (pica)" in resp
        assert "pica" in resp.lower()

        # Evidence-based guidance
        assert "sodium" in resp.lower() or "dash" in resp.lower() or "physician" in resp.lower()

        # Must NOT dump personal lab report
        assert "Key Findings & Out-of-Range Metrics" not in resp

    def test_pubmed_citations_synthesized_in_one_sentence_without_metadata_scraping(self):
        """
        Verifies that literature takeaways are synthesized into one plain-English sentence
        in the message body without printing raw PubMed scrapings, author affiliations,
        or conflict of interest blocks.
        """
        mock_citations = [
            {
                "pmid": "38210001",
                "title": "Clinical Guidelines for Mixed Dyslipidemia and Statin Therapy",
                "journal": "J Am Coll Cardiol",
                "year": "2024",
                "abstract": (
                    "Author information: (1)HealthCore Inc., Wilmington, DE. "
                    "Conflict of interest statement: None declared. "
                    "This 2024 clinical review confirms that lifestyle changes and statin medications "
                    "are the most effective first steps for lowering cholesterol and cardiovascular events."
                ),
                "url": "https://pubmed.ncbi.nlm.nih.gov/38210001/",
            }
        ]

        with patch("apps.assistant.services.pubmed_service.pubmed_service.search_pubmed") as mock_pubmed:
            mock_pubmed.return_value = {
                "status": "success",
                "citations": mock_citations,
                "total_results": 1,
            }

            self.client.force_authenticate(user=self.pat1_user)
            res = self.client.post(
                "/api/v1/assistant/chat/",
                {"prompt": "What are the first-line treatments for mixed dyslipidemia?"},
                format="json",
            )
            assert res.status_code == status.HTTP_200_OK
            data = res.json()

            # Technical metadata is returned in citations for the collapsible UI component
            assert len(data["citations"]) == 1
            assert data["citations"][0]["pmid"] == "38210001"

            resp = data["response"]
            # No raw scrapings or metadata headers in the message body
            assert "Author information:" not in resp
            assert "HealthCore Inc" not in resp
            assert "Conflict of interest statement:" not in resp
            assert "Relevant peer-reviewed literature:" not in resp
            assert "Key Finding:" not in resp

            # Synthesized plain-English takeaway sentence
            assert "statin" in resp.lower()
            assert "cholesterol" in resp.lower()

    def test_myth_busting_hot_lemon_water_and_baking_soda_not_hijacked_by_dyslipidemia(self):
        """
        Verifies that queries asking if hot lemon water and baking soda can cure diabetes
        and dissolve cholesterol overnight are NOT hijacked by the standard dyslipidemia template.
        Sentence 1 must directly address and refute the myth before offering sound guidance.
        """
        self.client.force_authenticate(user=self.pat1_user)
        res = self.client.post(
            "/api/v1/assistant/chat/",
            {"prompt": "Can drinking hot lemon water and baking soda cure my diabetes and dissolve cholesterol overnight?"},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        resp = data["response"]

        # MUST NOT be hijacked by generic dyslipidemia template opening
        assert "First-line management for mixed dyslipidemia focuses on" not in resp

        # MUST directly refute in sentence 1
        assert "No, drinking lemon water and baking soda cannot cure diabetes or dissolve cholesterol overnight" in resp
        assert "baking soda" in resp.lower()
        assert "sodium" in resp.lower()
        assert "plaque" in resp.lower()

        # Medically sound guidance included
        assert "statin" in resp.lower()
        assert "metformin" in resp.lower() or "carbohydrate" in resp.lower() or "physician" in resp.lower()

    def test_lab_explanation_consolidates_and_deduplicates_biomarkers(self):
        """
        Verifies that lab interpretation groups related biomarkers into single consolidated
        diagnostic sections rather than repeating the same explanation multiple times.
        """
        from apps.medical_records.models import LabReport, LabResult

        report = LabReport.objects.create(
            patient=self.pat1_user,
            title="Metabolic Profile Panel",
        )
        LabResult.objects.create(report=report, test_name="Fasting Blood Glucose", value="168", unit="mg/dL", flag="high")
        LabResult.objects.create(report=report, test_name="HbA1c", value="8.4", unit="%", flag="high")
        LabResult.objects.create(report=report, test_name="Total Cholesterol", value="242", unit="mg/dL", flag="high")
        LabResult.objects.create(report=report, test_name="Triglycerides", value="218", unit="mg/dL", flag="high")
        LabResult.objects.create(report=report, test_name="HDL", value="34", unit="mg/dL", flag="low")
        LabResult.objects.create(report=report, test_name="Serum Creatinine", value="1.38", unit="mg/dL", flag="high")

        self.client.force_authenticate(user=self.pat1_user)
        res = self.client.post(
            "/api/v1/assistant/chat/",
            {"prompt": "Please explain my latest lab results to me."},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        resp = data["response"]

        # Consolidated section headers
        assert "Glycemic Control" in resp
        assert "Lipid Panel" in resp
        assert "Kidney Function" in resp

        # Both Fasting Glucose and HbA1c in single Glycemic Control header
        assert "168 mg/dL" in resp
        assert "8.4" in resp

        # Cholesterol, Triglycerides, and HDL grouped in single Lipid Panel header
        assert "242 mg/dL" in resp
        assert "218 mg/dL" in resp
        assert "34 mg/dL" in resp

        # Creatinine in Kidney Function header
        assert "1.38 mg/dL" in resp

        # Verify that the explanation text is deduplicated (appears only ONCE, not 3 times or 2 times)
        assert resp.count("mixed dyslipidemia with elevated bad cholesterol") == 1
        assert resp.count("Elevated levels indicate poorly controlled high blood sugar") == 1
        assert resp.count("reduced kidney filtration") == 1



