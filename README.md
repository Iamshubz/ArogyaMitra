# ArogyaMitra

Healthcare in Your Language, Care for Everyone.

<<<<<<< HEAD
ArogyaMitra is a healthcare information and communication prototype for
patients, healthcare workers, and administrators. It is not a diagnostic or
prescribing system.
=======
## Stack

- Frontend: React, TypeScript, Vite, Axios
- Backend: FastAPI, Pydantic, SQLAlchemy, Alembic
- Database: PostgreSQL (SQLite is used by the automated tests)
- Authentication: JWT access tokens and Argon2 password hashing
- Storage: private Supabase Storage for medical documents

## Implemented features

- Authentication, profiles, preferred languages, and role-based access.
- Patient workspace with medical text simplification/translation, voice
  fallback, reminders, emergency contact `112`, health education, and bookmarks.
- Healthcare worker workspace with approved-worker and patient-grant checks,
  assigned patient search, authorized translation history, and follow-ups.
- Administrator workspace with user/access management, aggregate analytics,
  content lifecycle controls, and system monitoring.
- Provider-independent AI safety foundation with source-text preservation,
  review-required extraction, and explicit medical disclaimers.
- Private medical document metadata and download authorization.

## Local development

See [docs/SETUP.md](docs/SETUP.md) for PostgreSQL, backend, frontend, and
migration setup.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

In another terminal:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

API: `http://127.0.0.1:8000`
Swagger: `http://127.0.0.1:8000/docs`
Frontend: `http://localhost:5173`

## Verification commands

```bash
cd backend && .venv/bin/pytest -q
cd backend && .venv/bin/alembic check
cd frontend && npm run build
```

The final verified baseline is documented in the release checklist below.

## API groups

- `/api/v1/auth`, `/api/v1/users`, `/api/v1/health`
- `/api/v1/records`, `/api/v1/content`
- `/api/v1/ai`
- `/api/v1/reminders`, `/api/v1/education`, `/api/v1/emergency`, `/api/v1/voice`
- `/api/v1/worker`
- `/api/v1/admin`

## Safety and privacy

- Never commit `.env` files, service-role keys, JWT secrets, or patient data.
- Medical documents are stored through private storage paths, not public URLs.
- Patient access requires ownership, an administrator-created worker grant, or
  administrator role.
- AI output is informational, not a diagnosis or prescription.
- OCR, translation, and extracted entities require human verification.
- Reminder delivery remains unconfirmed until a notification provider confirms it.

## Phase 7 feature checklist

- [x] Authentication and profile flows
- [x] Patient, healthcare worker, and administrator role boundaries
- [x] Medical text translation and simplification foundation
- [x] Conservative medical entity extraction
- [x] Symptom guidance and emergency escalation
- [x] Browser speech recognition/synthesis fallback
- [x] Persistent reminders and explicit delivery status
- [x] Health education content and bookmarks
- [x] Worker patient management, translation history, and follow-ups
- [x] Admin analytics, content listing/deletion, and system monitoring
- [x] Alembic migrations through `0006_worker_admin_services`
- [x] Backend tests, frontend production build, and Alembic consistency checks
- [ ] Production OCR/LLM/translation provider configuration
- [ ] Confirmed email/SMS/push notification provider
- [ ] Browser-level visual regression testing in the deployment browser matrix
- [ ] Production observability, backups, retention, and incident runbooks
