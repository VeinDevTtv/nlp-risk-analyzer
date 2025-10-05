## NLP Risk Analyzer — Portfolio

### Summary
- **What**: End-to-end system that ingests finance news/headlines, detects mentioned assets, and scores risk using NLP (NER + sentiment + urgency + volatility heuristics). Exposes a REST API and a live dashboard with watchlists and charts.
- **Why**: Quickly assess headline-driven risk for tickers, portfolios, or alerts. Useful for traders, analysts, and ML ops experimenting with event-driven risk signals.
- **Tech**: Backend: Python + FastAPI; NLP: spaCy (NER), Hugging Face Transformers (FinBERT/financial sentiment); DB: Postgres + SQLAlchemy + Alembic; Workers: Celery/Redis (or APScheduler); Frontend: Next.js + Tailwind + Recharts; Containerization: Docker Compose; CI: GitHub Actions; Deploy: Vercel (frontend), Railway/Render (backend), Supabase/Neon (DB).

### Architecture
```mermaid
flowchart LR
  subgraph Client
    U[User / Browser]
  end

  subgraph Frontend [Next.js Dashboard]
    FE[Watchlists • Ticker Pages • Charts]
  end

  subgraph Backend [FastAPI]
    API[/REST API v1/]
  end

  subgraph Workers [Ingestion + NLP]
    SCH[Scheduler]
    ING[News Fetcher]
    NLP[NLP Processor\n(spaCy + FinBERT)]
  end

  subgraph DB[(Postgres)]
    TBL1[(headlines)]
    TBL2[(mentions)]
    TBL3[(risk_scores)]
    TBL4[(tickers)]
  end

  U --> FE
  FE -->|fetch| API
  API --> DB
  SCH --> ING --> DB
  SCH --> NLP --> DB
  API --> FE
```

Alternative: include a binary diagram at `docs/architecture.png` and reference it here.

### How to generate screenshots locally
Prereqs: Docker and Docker Compose.

1) Start the stack
```bash
cd infra
docker-compose up -d --build
```

2) Open the dashboard
- Navigate to `http://localhost:3000/ticker/AAPL` (replace `AAPL` as needed).
- You should see the ticker page with a risk gauge, latest headlines, and a time series chart.

3) Take screenshots
- Full dashboard: `http://localhost:3000/`
- Ticker detail: `http://localhost:3000/ticker/AAPL`
- Backend health: `http://localhost:8000/docs` (FastAPI swagger)

Tip: If data is empty, let the scheduler run for a minute, or run ingestion manually (see `backend/app/workers/scheduler.py` or call the analyze endpoint in `backend/app/api/v1/analyze.py`).

### 90–120s demo script
Use this as a tight run-of-show to record a short demo.

- 0:00–0:10 — Intro
  - “This is the NLP Risk Analyzer. It ingests finance headlines and scores ticker risk in real-time.”

- 0:10–0:25 — Problem framing
  - “News moves markets. Traders and analysts need fast, structured signals from messy text.”

- 0:25–0:55 — Live demo
  - Show watchlist on the homepage.
  - Click `AAPL` to open `/ticker/AAPL`.
  - Highlight the risk gauge, recent headlines with asset mentions, and the risk timeseries chart.

- 0:55–1:15 — How it works (code tour)
  - Point out FastAPI endpoints in `backend/app/api/v1/` (e.g., `analyze.py`).
  - Show NLP pipeline in `backend/app/nlp/processor.py` (spaCy NER + FinBERT sentiment + heuristics).
  - Show ingestion/scheduling in `backend/app/workers/scheduler.py` and `ingest/news_fetcher.py`.
  - Briefly mention Postgres models in `backend/app/models/` and Alembic migrations.

- 1:15–1:30 — Backtest + CTA
  - Open one of the generated reports under `backend/backtest_reports/`.
  - Close with “Repo link in the description—try the Docker Compose setup and extend the scoring rules.”

### Blog template — “How I built the NLP Risk Analyzer”

Use this outline to write a short technical blog post.

#### 1) Motivation
- The gap between raw headlines and actionable risk signals.
- Constraints: near-real-time, explainability, reproducibility.

#### 2) Architecture overview
- Frontend (Next.js + Tailwind), Backend (FastAPI), NLP (spaCy + FinBERT), Workers (Celery/APScheduler), DB (Postgres), CI/CD, Docker.
```text
Client → Next.js → FastAPI → Postgres
             ↑            ↑
       Charts/Pages   Workers (Ingest + NLP)
```

#### 3) Backend API (FastAPI)
```python
from fastapi import FastAPI
from app.api.v1 import analyze, status, watchlist

app = FastAPI()
app.include_router(analyze.router, prefix="/api/v1")
app.include_router(status.router, prefix="/api/v1")
app.include_router(watchlist.router, prefix="/api/v1")
```

#### 4) NLP pipeline (spaCy + FinBERT)
```python
import spacy
from transformers import pipeline

nlp = spacy.load("en_core_web_sm")
sentiment = pipeline("text-classification", model="ProsusAI/finbert")

def score_headline(text: str) -> dict:
    doc = nlp(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    s = sentiment(text)[0]
    # simple heuristic combining polarity + entity presence
    polarity = {"positive": 1, "neutral": 0, "negative": -1}[s["label"].lower()]
    urgency = 1 if any(tok.lemma_.lower() in {"downgrade", "bankrupt", "probe"} for tok in doc) else 0
    risk = max(0.0, min(1.0, 0.5 + 0.3*polarity + 0.2*urgency))
    return {"entities": entities, "sentiment": s, "risk": risk}
```

#### 5) Frontend snippets (Next.js)
```tsx
// Example data fetcher
export async function getRisk(symbol: string) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/analyze?symbol=${symbol}`);
  return res.json();
}
```

#### 6) Ingestion and scheduling
```python
# Trigger periodic ingestion and processing
def run_cycle():
    fetch_new_headlines()
    process_unprocessed_headlines()
```

#### 7) Backtesting highlights
- Describe approach, sample period, metrics, and how results inform heuristics.
- Include a figure or link to `backend/backtest_reports/`.

#### 8) Deployment notes
- Compose for local; Vercel (FE), Railway/Render (BE), and managed Postgres.

#### 9) Lessons learned and next steps
- Entity linking to tickers, volatility-aware scoring, alerting via webhooks.

---

For more, see the main `README.md` and `infra/` for Docker Compose.


