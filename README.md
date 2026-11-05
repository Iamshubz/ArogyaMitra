# ArogyaMitra

Healthcare in Your Language, Care for Everyone.

AI-Driven Healthcare Assistance Platform for Rural
Communities with Multilingual Medical
Communication Support.

## Stack
- Frontend: React + TypeScript + Vite
- Backend: FastAPI + Pydantic + SQLAlchemy
- Database: PostgreSQL
- Authentication: JWT access tokens with Argon2 password hashing
- Migrations: Alembic
- Later phases: OCR, NLP/LLM simplification, Indian-language translation, speech, reminders, Docker

## Milestones
1. Foundation: repository, frontend/backend setup, database connectivity and health endpoint
2. Weeks 1–2: authentication, patient/worker profiles, language preference and profile management (current)
3. Weeks 3–4: OCR, medical entity extraction, simplification, translation and health knowledge content
4. Weeks 5–6: speech input/output, verified medication schedules, reminders and emergency information
5. Weeks 7–8: mobile client, worker/admin portals, integration testing, documentation and deployment

## Quick start
See `docs/SETUP.md` for local setup and `docs/ARCHITECTURE.md` for system design.

## Milestone 1 APIs
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout`
- `GET /api/v1/users/profile`
- `PUT /api/v1/users/profile`
- `GET /api/v1/health`

## Safety
This software is an information and communication aid, not a diagnostic or prescribing system. Never generate or change medicine doses. Extracted prescription instructions must be reviewed by an authorized healthcare professional before medication schedules or reminders are activated. Treat uncertain OCR as requiring human review.
