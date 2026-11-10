# ArogyaMitra

**Healthcare in Your Language, Care for Everyone.**

ArogyaMitra is a role-based healthcare support platform for patients, healthcare
workers, and administrators. It helps patients understand health information,
manage reminders, access education, and communicate with care teams. It is an
information and coordination tool; it does not replace a qualified healthcare
professional.

## What the platform provides

- Patient, healthcare-worker, and administrator accounts
- JWT authentication with role-based access control
- Patient profiles and language preferences
- Medication reminders and status tracking
- Medical document, prescription, and report workflows
- AI-assisted chat, text simplification, translation, symptom guidance, and
  medical-image explanation
- Healthcare education and emergency contacts
- Worker patient assignment and follow-up monitoring
- Administrator analytics, content management, and system monitoring
- Responsive React and TypeScript web interface

AI output is informational only. Patients must confirm medical information,
prescriptions, and treatment decisions with a qualified healthcare professional.

## Technology

| Area | Technology |
|---|---|
| Frontend | React, TypeScript, Vite, Axios |
| Backend | Python, FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL |
| Migrations | Alembic |
| Authentication | JWT and Argon2 password hashing |
| Storage | Private Supabase Storage integration |
| AI | OpenAI API through a backend-only adapter |

## Repository structure

```text
backend/
  app/
    api/          HTTP routes
    core/         Configuration and security
    db/           Database models and sessions
    schemas/      Request and response contracts
    services/     Business logic and AI integrations
  alembic/        Database migrations
  tests/          Backend tests
frontend/
  src/
    App.tsx       Application UI and role-based views
    services/     Backend API client
    styles.css    Application styles
docs/             Setup, architecture, and deployment guides
```

## Requirements

- Python 3.11+
- Node.js 20 LTS+
- npm
- PostgreSQL 15+
- Git

## Local setup

### 1. Configure the database

Create a PostgreSQL database and user, then set the connection string in
`backend/.env`.

### 2. Configure and start the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\Activate.ps1       # Windows PowerShell
pip install -r requirements.txt
cp .env.example .env
```

Update `backend/.env` with local values. At minimum, configure:

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/healthcare_db
JWT_SECRET_KEY=use-a-long-random-secret
FRONTEND_ORIGIN=http://localhost:5173
```

For AI chat and medical-image analysis, also configure:

```env
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4o-mini
```

Never commit `.env`, API keys, database passwords, JWT secrets, or patient
information.

Apply migrations and start the API:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

The backend runs at `http://127.0.0.1:8000`.

Useful endpoints:

- Health check: `http://127.0.0.1:8000/api/v1/health`
- Swagger documentation: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

### 3. Start the frontend

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:5173`.

If the frontend and backend use different origins, set:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Account roles

### Patient

Patients can manage their profile, reminders, health education, emergency
contacts, AI assistance, and their own authorized medical information.

### Healthcare worker

Healthcare workers can access only administrator-assigned patients and must be
approved before using protected worker services.

### Administrator

Administrators manage platform content, approve healthcare workers, grant
patient access, and view operational analytics. Admin accounts are not created
through public registration.

## Testing and production build

Run backend tests:

```bash
cd backend
.venv/bin/pytest -q
```

Build the frontend:

```bash
cd frontend
npm run build
```

Check migrations:

```bash
cd backend
.venv/bin/alembic check
```

## Production checklist

- Use `ENVIRONMENT=production`.
- Use a unique JWT secret of at least 32 characters.
- Store secrets in a managed secret store, not in source control.
- Restrict `FRONTEND_ORIGIN` to the deployed frontend origin.
- Serve the API and frontend over HTTPS.
- Keep Supabase service-role credentials backend-only.
- Use a private storage bucket and authorization checks for every document.
- Back up PostgreSQL and define data retention and deletion policies.
- Monitor errors without logging tokens, credentials, or medical text.
- Review health education and AI-assisted content before relying on it
  clinically.

More detailed operational guidance is available in
[`docs/SETUP.md`](docs/SETUP.md), [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md),
and [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).
