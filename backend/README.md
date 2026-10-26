# MediCare: Intelligent Clinical Decision Support System — Backend (PART 1)

This repository contains the backend core for **MediCare**, an Intelligent Clinical Decision Support System (CDSS) built using Django 5.x, Django REST Framework, PostgreSQL 16.x, and SimpleJWT.

---

## 1. Architecture Overview

```
backend/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
├── MILESTONE_MAP.md
├── SRS_TRACEABILITY.md
├── Dockerfile                  # Single canonical Dockerfile
├── docker-compose.yml          # Single canonical Docker Compose configuration
│
├── config/
│   ├── __init__.py
│   ├── settings.py             # Django settings with PostgreSQL & JWT configuration
│   ├── urls.py                 # Health check & canonical API route registrations
│   ├── asgi.py
│   └── wsgi.py
│
├── core/
│   ├── __init__.py
│   ├── permissions.py          # IsPatient, IsDoctor, IsAdmin, doctor_can_access_patient
│   ├── exceptions.py           # Standardized JSON error response handler
│   ├── pagination.py           # StandardResultsSetPagination (page_size=10)
│   └── utilities.py            # DB ping, magic byte file validation, safe file naming
│
├── apps/
│   ├── accounts/               # Custom User (email-based), JWT Auth, Me endpoints
│   ├── patients/               # PatientProfile, DB-backed Dashboard aggregations
│   ├── doctors/                # DoctorProfile, ClinicalNote, Doctor Insights
│   ├── appointments/           # Appointment scheduling, status tracking, access control
│   ├── medical_records/        # MedicalRecord, LabReport, LabResult, multipart uploads
│   ├── predictions/            # DiseasePrediction & SymptomAnalysis storage models
│   ├── medicines/              # Medication model & prescription tracking
│   ├── assistant/              # ChatConversation & ChatMessage storage models
│   ├── audit_logs/             # AuditLog model & centralized server-side logging
│   └── admin_panel/            # Admin user management, DB analytics, audit viewer
│
├── deployment/
│   └── nginx.conf              # Single canonical Nginx reverse proxy configuration
│
└── tests/                      # Automated pytest test suite (29 tests)
```

---

## 2. Prerequisites & Setup

- **Python**: 3.12+ (3.13 supported)
- **PostgreSQL**: 16.x (or Docker)
- **Node.js**: 20+ (for protected React frontend)

### Installation & Local Setup

```powershell
# 1. Navigate to backend directory
cd backend

# 2. Configure environment variables
copy .env.example .env

# 3. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run database migrations
python manage.py makemigrations
python manage.py migrate

# 6. Start development server
python manage.py runserver
```

---

## 3. Database Configuration

PostgreSQL is the primary database specified by the MediCare SRS.

Required environment variables:
- `DB_NAME` (or `POSTGRES_DB`)
- `DB_USER` (or `POSTGRES_USER`)
- `DB_PASSWORD` (or `POSTGRES_PASSWORD`)
- `DB_HOST` (or `POSTGRES_HOST`, default: `localhost`)
- `DB_PORT` (or `POSTGRES_PORT`, default: `5432`)

If any required PostgreSQL variables are missing, Django raises an explicit `ImproperlyConfigured` exception.

> **Note**: For running isolated unit tests without an active live PostgreSQL connection, set the explicit flag:
> ```powershell
> $env:USE_SQLITE_TESTS="true"
> ```

---

## 4. Authentication & Authorization

### Authentication Flow (SimpleJWT)
- **Email-based identifier**: The custom `User` model does not use usernames; emails are strictly unique.
- **Access token lifetime**: 30 minutes (configurable via `JWT_ACCESS_MINUTES`).
- **Refresh token lifetime**: 7 days (configurable via `JWT_REFRESH_DAYS`).
- **Token rotation & blacklisting**: Enabled. Logging out explicitly blacklists the refresh token.

### Application Roles & Permissions
- **Roles**: `patient`, `doctor`, `admin`.
- **Application Admin vs Django Staff**: `is_staff` does **NOT** equal application `admin`. Application API authorization requires `request.user.role == "admin"`.
- **Doctor-Patient Authorization Boundary**: Enforced via `doctor_can_access_patient(doctor, patient)`. Access is granted only if the doctor has an active/completed appointment, has authored clinical notes, or has prescribed medications for the patient.
- **Patient Data Isolation**: Object-level permissions prevent patients from accessing another patient's records or appointments.
- **Role Escalation Prevention**: Normal users cannot update their own role, `is_staff`, or `is_superuser` via request payloads.

---

## 5. API Endpoints Reference

All endpoints are prefixed with `/api/v1/`.

### Health & Auth
- `GET  /api/v1/health/` — Health & DB readiness check
- `POST /api/v1/auth/register/` — Register patient or doctor
- `POST /api/v1/auth/login/` — Obtain JWT access & refresh tokens
- `POST /api/v1/auth/refresh/` — Refresh access token
- `POST /api/v1/auth/logout/` — Blacklist refresh token
- `GET  /api/v1/auth/me/` — Retrieve authenticated user profile
- `PATCH /api/v1/auth/me/` — Update user profile

### Patient Workflows
- `GET   /api/v1/patient/profile/` — Own profile details
- `PATCH /api/v1/patient/profile/` — Update own profile
- `GET   /api/v1/patient/dashboard/` — Real DB-backed patient summary
- `GET   /api/v1/patient/appointments/` — List own appointments
- `POST  /api/v1/patient/appointments/` — Book an appointment
- `PATCH /api/v1/patient/appointments/<id>/` — Reschedule or cancel appointment
- `GET   /api/v1/patient/medical-records/` — List own medical records
- `GET   /api/v1/patient/lab-tests/` — List own lab reports & test results
- `POST  /api/v1/patient/reports/upload/` — Upload lab report (validated)
- `GET   /api/v1/patient/medications/` — List own medications
- `GET   /api/v1/patient/predictions/` — Prediction history
- `GET   /api/v1/patient/symptom-analyses/` — Symptom analysis history

### Doctor Workflows
- `GET  /api/v1/doctor/profile/` — Own doctor profile
- `PATCH /api/v1/doctor/profile/` — Update doctor profile
- `GET  /api/v1/doctor/patients/` — List authorized patients
- `GET  /api/v1/doctor/patients/<id>/` — Authorized patient detail
- `GET  /api/v1/doctor/patients/<id>/records/` — Authorized patient records
- `GET  /api/v1/doctor/patients/<id>/reports/` — Authorized patient reports
- `POST /api/v1/doctor/patients/<id>/clinical-notes/` — Record clinical note
- `GET  /api/v1/doctor/appointments/` — Scheduled appointments
- `GET  /api/v1/doctor/insights/` — Real DB-derived decision support metrics

### Admin Workflows
- `GET   /api/v1/admin/users/` — Paginated user list with filters
- `PATCH /api/v1/admin/users/<id>/` — Update user status / role
- `GET   /api/v1/admin/audit-logs/` — Paginated audit log records
- `GET   /api/v1/admin/analytics/` — Real DB-derived platform metrics

### Assistant & RAG Workflows
- `POST /api/v1/assistant/chat/` — Evidence-grounded RAG with PubMed citations and conversation persistence
- `GET  /api/v1/assistant/history/` — Conversation & message history

### Medicines & Pharmacological Intelligence Workflows
- `GET  /api/v1/medicines/` — List active medications
- `POST /api/v1/medicines/` — Prescribe or add medication
- `GET  /api/v1/medicines/<id>/` — Medication detail
- `POST /api/v1/medicines/interactions/` — Unified pairwise and patient-prescriptions interaction analysis
- `GET  /api/v1/medicines/openfda/reactions/` — OpenFDA adverse drug reactions and boxed warnings
- `POST /api/v1/medicines/openfda/interactions/` — OpenFDA pairwise interactions


---

## 6. Strong File Validation (Medical Reports)

Uploaded lab reports are verified by:
1. **File size**: Max 10 MB.
2. **File extension**: `.pdf`, `.jpeg`, `.jpg`, `.png`, `.webp`.
3. **MIME type**: `application/pdf`, `image/jpeg`, `image/png`, `image/webp`.
4. **Magic Byte Signatures**:
   - PDF: `%PDF`
   - PNG: `\x89PNG\r\n\x1a\n`
   - JPEG: `\xff\xd8\xff`
   - WebP: `RIFF...WEBP`
5. **Safe Storage**: Filenames are sanitized and saved using UUID4 server-side names under `media/reports/%Y/%m/`.

---

## 7. Running Automated Tests

Run the full pytest test suite:

```powershell
# Using SQLite test database for isolated testing
$env:USE_SQLITE_TESTS="true"
.\.venv\Scripts\pytest
```

**Test Results Summary**:
- Total tests: **29**
- Passed: **29 (100%)**
- Time: ~1.5 minutes

---

## 8. Docker Deployment

Single canonical Docker Compose configuration:

```bash
docker-compose up --build -d
```

Services:
- `db`: PostgreSQL 16 Alpine with healthcheck.
- `backend`: Gunicorn WSGI server running 3 workers.
- `nginx`: Alpine reverse proxy routing `/api/`, `/admin/`, `/static/`, `/media/`.

---

## 9. Google Gemini API Integration & Clinical Decision Support

MediCare integrates Google Gemini API using the official Google Gen AI SDK (`google-genai`) for natural-language clinical explanation, patient communication, and uncertainty identification.

### Key Capabilities
1. **Official Google Gen AI SDK**: Uses `google-genai>=1.0.0` with dynamic model selection via `GEMINI_MODEL` (default: `gemini-3.5-flash`, free-tier eligible).
2. **Independent Emergency Triage Protocol**: A safety-first rule-based triage layer executes **before** calling external LLMs or PubMed. Catches red flags for stroke (sudden facial droop, unilateral weakness, slurred speech), acute cardiac distress (severe chest pressure with breathlessness or sweating), respiratory failure, and anaphylaxis.
3. **Stroke Emergency Instructions**: Explicitly directs patients to call emergency dispatch immediately (911 / 112 / 999), record the exact time of onset or when last known well, avoid driving themselves, and avoid delaying care.
4. **Multi-Turn Conversation Freshness**: Every message triggers fresh symptom extraction and disease inference. Previous conversation history provides dialogue context only; diagnoses from prior turns are never reused for unrelated symptoms.
5. **NCBI PubMed RAG Grounding**: Generates responses strictly grounded in peer-reviewed biomedical literature without fabricated PMIDs or hallucinated clinical citations. For emergency triage, PubMed lookups are bypassed to avoid attaching irrelevant citations (such as pericarditis or depression).
6. **Calibrated Confidence**: Confidence percentages are only displayed when provided by the verified machine learning classifier. Missing confidence scores are never fabricated.

### Environment Configuration

Add the following environment variables to your `.env` file (see `.env.example`):

```bash
# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash

# Optional: Set LLM_PROVIDER to force provider selection (gemini, openai, or extractive)
LLM_PROVIDER=gemini
```

### Obtaining an API Key from Google AI Studio
1. Visit [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google account.
3. Click **"Get API key"** and create an API key in a Google Cloud project.
4. Copy the key and set `GEMINI_API_KEY=your_key` in `backend/.env`.
5. Keep your key confidential: `.env` is ignored by Git and must never be committed.

### Structured Response Schema
The `/api/v1/assistant/chat/` endpoint returns a structured response payload:
```json
{
  "conversation_id": 12,
  "message_id": 45,
  "query": "Repeated sneezing, itchy nose, clear watery nasal discharge",
  "response": "Clinical impression and literature synthesis...",
  "citations": [ ... ],
  "literature_references": [ ... ],
  "emergency_triage": {
    "is_emergency": false,
    "categories": [],
    "status": "NON_EMERGENCY"
  },
  "urgency_level": "EVALUATION_RECOMMENDED",
  "input_summary": "repeated sneezing, itchy nose...",
  "possible_conditions": [
    { "condition": "Allergic Rhinitis", "status": "candidate_impression", "confidence": 0.8527 }
  ],
  "supporting_symptoms": ["sneezing", "nasal_discharge", "itchy_nose"],
  "missing_information": [ ... ],
  "recommended_next_steps": [ ... ],
  "disclaimer": "MANDATORY REGULATORY DISCLAIMER: This system provides AI-assisted clinical decision support..."
}
```

### Regulatory Disclaimer & Safety Limitations
> **CRITICAL MEDICAL DISCLAIMER**: MediCare is an educational clinical decision-support prototype (Software as a Medical Device, SaMD educational tier). It does NOT provide confirmed diagnoses or medical advice. Rule-based emergency detection relies on clinical pattern matching and cannot replace qualified in-person emergency physician triage. Always consult a licensed healthcare professional.

