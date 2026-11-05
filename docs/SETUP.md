# Local setup instructions

## Prerequisites
- Python 3.11 or newer
- Node.js 20 LTS or newer and npm
- PostgreSQL 15 or newer
- Git
- VS Code (recommended)

## 1. Database
Create a local PostgreSQL database and user. Example in `psql` as a database administrator:

```sql
CREATE USER healthcare_user WITH PASSWORD 'replace-with-a-local-password';
CREATE DATABASE healthcare_db OWNER healthcare_user;
```

Use a unique local password. Do not commit real credentials.

## 2. Backend
From the repository root:

```bash
cd backend
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
# Edit DATABASE_URL and JWT_SECRET_KEY in .env for your local PostgreSQL credentials.
alembic upgrade head
uvicorn app.main:app --reload
```

Backend: `http://127.0.0.1:8000`  
Swagger docs: `http://127.0.0.1:8000/docs`  
Health check: `http://127.0.0.1:8000/api/v1/health`

## 3. Frontend
Open a second terminal from the repository root:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend: `http://localhost:5173`

## 4. Verify Milestone 1
1. Confirm PostgreSQL is running.
2. Start FastAPI and open `/api/v1/health`; expect `{"status":"ok","database":"connected"}`.
3. Start Vite and open `http://localhost:5173`.
4. The ArogyaMitra login screen should load and show backend connectivity after sign-in.

## Authentication
Registration supports patient and healthcare-worker accounts. Admin accounts are intentionally not self-registerable; create them through a controlled database or administration workflow. Passwords are hashed with Argon2 and access tokens are signed using `JWT_SECRET_KEY`.

## Troubleshooting
- PostgreSQL connection refused: start the PostgreSQL service and verify host/port.
- Authentication failed: check the username/password in `backend/.env`.
- Frontend says API unavailable: ensure FastAPI is running on port 8000 and the Vite proxy is enabled.
- `npm` or `python` not found: install the required runtime and reopen the terminal.
