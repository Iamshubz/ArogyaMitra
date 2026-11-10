# Deployment runbook

## Backend

1. Provision PostgreSQL and a private Supabase Storage bucket.
2. Deploy the `backend` directory with Python 3.11+.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables from `.env.example`:
   - `ENVIRONMENT=production`
   - A unique `DATABASE_URL`
   - A random `JWT_SECRET_KEY` with at least 32 characters
   - Restricted `FRONTEND_ORIGIN`
   - `SUPABASE_URL`, backend-only `SUPABASE_SERVICE_ROLE_KEY`, and
     `STORAGE_BUCKET`
5. Apply migrations:

   ```bash
   alembic upgrade head
   ```

6. Start the API with a production process manager:

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

Terminate TLS at the hosting platform or reverse proxy. Do not expose the
Supabase service-role key to the frontend.

## Frontend

1. Set `VITE_API_BASE_URL` to the public backend origin if the frontend and API
   are hosted on different origins. Leave it empty when a same-origin reverse
   proxy serves `/api`.
2. Install and build:

   ```bash
   npm ci
   npm run build
   ```

3. Serve `frontend/dist` using a static host.

Configure the backend CORS `FRONTEND_ORIGIN` to exactly match the deployed
frontend origin.

## Release checks

Run from the repository root:

```bash
cd backend && .venv/bin/pytest -q
cd backend && .venv/bin/alembic check
cd frontend && npm run build
```

Then verify:

- `GET /api/v1/health` reports a connected database.
- Login, logout, and expired-token behavior work.
- A patient cannot access another patient's records.
- An unapproved worker cannot access assigned-patient APIs.
- An admin can approve a worker and grant patient access.
- Private document downloads remain authorization-protected.
- Browser speech fallback works where speech APIs are unavailable.
- Reminder delivery is not reported as successful without provider confirmation.

## Operations

- Rotate JWT and Supabase secrets through the hosting secret manager.
- Monitor API/database/storage failures without logging health details or tokens.
- Back up PostgreSQL and define retention/deletion policies before real patient
  data is used.
- Keep health content medically reviewed and track its source/review status.
