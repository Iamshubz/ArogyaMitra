# ArogyaMitra technical architecture

> Healthcare in Your Language, Care for Everyone.

## 1. High-level architecture

```text
Patient / Healthcare Worker / Admin
                 |
                 v
      React + TypeScript Web App
                 |
          HTTPS / REST JSON
                 |
                 v
          FastAPI Application
          |       |        |
          |       |        +--> Reminder/notification service (later)
          |       +-----------> AI orchestration services (later)
          +-------------------> JWT authentication and domain services
                 |
                 v
       SQLAlchemy + PostgreSQL
                 |
                 +--> Document metadata; binary files stored separately

AI services (later): OCR -> extraction -> human verification -> simplification
                    -> translation -> text-to-speech / speech-to-text
```

## 2. Backend module boundaries
- `api`: versioned HTTP endpoints.
- `core`: configuration and shared security utilities.
- `db`: database engine, session lifecycle and SQLAlchemy models.
- `models`: SQLAlchemy persistence models.
- `schemas`: Pydantic request/response contracts.
- `alembic`: versioned database migrations.
- `services`: business logic; AI providers will be adapters here.

## 3. Initial data model plan

| Entity | Key fields | Notes |
|---|---|---|
| User | id, email, password_hash, role, is_active | Shared identity; never store plaintext passwords |
| PatientProfile | user_id, age, date_of_birth | Patient-specific profile |
| HealthcareWorkerProfile | user_id, facility_name, specialization | Healthcare worker profile |
| LanguagePreference | code, name | Supported user language |
| MedicalDocument | id, patient_id, storage_key, content_type, status | Store file bytes in private object/local storage, not as public URLs |
| ExtractedMedicalData | document_id, extracted_text, confidence, review_status | OCR output is untrusted until reviewed |
| Translation | document_id, source_language, target_language, translated_text | Preserve original text and translation separately |
| MedicationSchedule | patient_id, verified_by, instructions, start/end | Only created from clinician-verified instructions |
| Reminder | schedule_id, due_at, status | Notification delivery record |
| HealthContent | title, language, topic, reviewed_by, reviewed_at | Approved education content |
| Notification | user_id, type, message, read_at | Avoid exposing sensitive medical details in lock-screen text |

## 4. Security and safety requirements
- Use HTTPS in deployment and JWT access tokens with short expiry; add refresh-token rotation before production.
- Hash passwords with Argon2; never log credentials, tokens, prescription text, or health details.
- Enforce role-based authorization and patient-level ownership checks on every document endpoint.
- Validate upload size, extension and actual file type; scan files; store them outside the public web root.
- Collect only necessary personal data; define retention/deletion and backup policies.
- Encrypt backups and storage; keep secrets in environment variables/secret manager.
- OCR, translation and generated explanations can be wrong. Display source text alongside transformed text and require human verification for ambiguous prescription details.
- Do not diagnose, prescribe, recommend a dosage, or change a clinician's instructions.

## 5. API conventions
- Prefix: `/api/v1`
- JSON responses for application data.
- OpenAPI docs at `/docs` in local development.
- Initial endpoints: `GET /api/v1/health`, `/api/v1/auth/*` and `/api/v1/users/profile`.
- Planned endpoints: `/auth`, `/patients/me`, `/workers/me`, `/documents`, `/translations`, `/medication-schedules`, `/reminders`, `/health-content`, `/admin/analytics`.
