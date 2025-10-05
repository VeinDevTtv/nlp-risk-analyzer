### NLP Risk Analyzer — Production Deployment Guide

This guide outlines a practical production setup using managed services with minimal ops burden. Feel free to mix providers as needed.

## Backend API (FastAPI)

- Build a container image and deploy to a managed container platform (Railway or Render).
- Expose port via the process manager; both platforms will inject `$PORT`.

Example Dockerfile (already provided at `backend/Dockerfile` — shown here for clarity):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app

ENV PYTHONUNBUFFERED=1 \
    PORT=8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
```

Startup command (Railway/Render):

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Required environment variables (see "Environment Checklist" below).

## Database (Postgres)

Use a managed Postgres: Supabase or Neon. Provision a database and copy the connection string as `DATABASE_URL`.

Examples:

```bash
# Supabase
DATABASE_URL="postgresql://postgres:<PASSWORD>@db.<proj>.supabase.co:5432/postgres"

# Neon
DATABASE_URL="postgresql://<user>:<password>@<host>.neon.tech/<db>?sslmode=require"
```

Run Alembic migrations on deploy (Railway/Render build/exec step):

```bash
alembic upgrade head
```

## Redis

Use Upstash or Redis Cloud. Supply the URL via `REDIS_URL`.

Examples:

```bash
# Upstash (TLS URL)
REDIS_URL="rediss://:<PASSWORD>@<id>.upstash.io:6379"

# Redis Cloud
REDIS_URL="rediss://:<PASSWORD>@<host>:<port"
```

## Frontend (Next.js on Vercel)

- Import the `frontend/` directory in Vercel.
- Framework Preset: Next.js.
- Environment variables: set `NEXT_PUBLIC_API_URL` to your backend public base URL (e.g., `https://api.example.com`).
- One-click deploy from main branch.

## CI/CD (GitHub Actions)

- CI is set up to run tests and lint for backend and frontend.
- Optional: add deploy steps on merge to `main` using provider CLIs or HTTP deploy hooks.

Examples (conceptual):

```yaml
# Railway: use railway CLI (requires RAILWAY_TOKEN secret)
- name: Deploy API to Railway
  run: |
    npm i -g @railway/cli
    railway up --service api
  working-directory: backend
  env:
    RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

# Render: trigger deploy hook (RENDER_SERVICE_HOOK_URL secret)
- name: Trigger Render deploy
  run: curl -X POST "$RENDER_SERVICE_HOOK_URL"
  env:
    RENDER_SERVICE_HOOK_URL: ${{ secrets.RENDER_SERVICE_HOOK_URL }}
```

## Environment Checklist

Backend/API:
- DATABASE_URL: Postgres connection string
- REDIS_URL: Redis connection string (optional if no Celery/queues)
- NEWSAPI_KEY: optional, for news ingestion
- CORS_ALLOW_ORIGINS: optional comma-separated origins

Frontend (Vercel):
- NEXT_PUBLIC_API_URL: public base URL of backend API

CI/CD Secrets (GitHub):
- RAILWAY_TOKEN or RENDER_SERVICE_HOOK_URL (if auto-deploy is desired)

## Sample Secrets Templates

See `infra/secrets.example` for a provider-agnostic template and per-provider examples.


