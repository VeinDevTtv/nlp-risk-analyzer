NLP Risk Analyzer — Demo Runbook

Audience: quick product demo (3–7 minutes) on Windows. Focus: API scoring, health, and prebuilt backtest report. Optional: UI shell.

1) Prereqs
- Windows 10/11, PowerShell
- Docker Desktop (for the easiest run)
- Optional local dev: Python 3.11, Node 20

2) Start services (recommended: Docker Compose)
- In PowerShell:
```powershell
cd infra
docker-compose up --build
# Backend: http://localhost:8000  (FastAPI docs at /docs)
# Frontend: http://localhost:3000
# Postgres: 5432, Redis: 6379, pgAdmin: http://localhost:5050
```

Alternative: Local dev (backend only for API demo)
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Use a local SQLite DB (no migrations required for /v1/analyze)
$env:DATABASE_URL = "sqlite+pysqlite:///dev.db"
uvicorn app.main:app --reload --port 8000
```

3) Health check and API docs
- Health: `http://localhost:8000/health`  → { "status": "ok" }
- API docs: `http://localhost:8000/docs` (FastAPI Swagger UI)

4) Core demo: Analyze a headline
- In Swagger UI: POST `/v1/analyze` with body:
```json
{ "text": "BREAKING: AAPL plunges after earnings miss" }
```
- Show response fields: `entities`, `sentiment` (−1..1), `urgency` (0..1), `volatility` (0..1), `risk_percent` (0..100)

PowerShell one-liner (optional):
```powershell
$body = @{ text = "BREAKING: AAPL plunges after earnings miss" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/v1/analyze -Body $body -ContentType 'application/json'
```

5) Show the backtest report (prebuilt)
- Open in Explorer: `backend\backtest_reports\AAPL_2024-01-01_2024-02-01_report.html`
- Mention artifacts: PNG charts and CSV in the same folder

Optional: Regenerate demo artifacts
```powershell
cd backend
python scripts/run_demo_backtest.py
```
(This uses SQLite automatically and writes outputs under `backend/backtest_reports/`.)

6) Optional frontend tour (UI shell)
- `http://localhost:3000`
- Show search (navigate to `/ticker/AAPL`) and watchlist cards.
- Note: risk API `/v1/risk/{symbol}` is not wired in this build; UI will load shell only.

7) (If you want auth/watchlist demo)
- Requires DB migrations (Postgres via Docker Compose).
- In Swagger: `/v1/auth/signup` → copy `access_token`
- Use `Authorization: Bearer <token>` for `/v1/watchlist` GET/POST/DELETE

8) Recording checklist (Windows)
- Audio: select mic; test levels
- Resolution: 1920×1080 (30 fps is fine), text at 125–150% zoom
- Hide sensitive info, close noisy apps, set dark/light mode as you prefer

Recorders
- Xbox Game Bar: Win+G → Capture (Win+Alt+R start/stop)
- OBS Studio: Display Capture → 1080p, 30fps, Simple output, MKV or MP4

Suggested narration (3–7 min)
1) One-liner: “NLP Risk Analyzer ingests finance headlines, detects tickers, and scores risk.”
2) Start services (Docker), show `/health` and `/docs`.
3) Call `/v1/analyze` with an example; highlight fields and ranges.
4) Open the AAPL backtest HTML; point out metrics and charts.
5) Optional: briefly show the frontend shell and roadmap for risk endpoint.
6) Close with deployment notes (Vercel + Railway/Render) and next steps.


