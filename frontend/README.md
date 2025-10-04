# NLP Risk Analyzer Frontend

Next.js dashboard for viewing risk scores, time series, and recent headlines.

## Prerequisites

- Node.js 18+
- Backend API running (FastAPI) and accessible via `NEXT_PUBLIC_API_URL`

## Setup

```bash
cd frontend
npm install
cp ../.env.example .env.local # adjust if needed
```

Edit `.env.local` and set:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Development

```bash
npm run dev
```

App runs on `http://localhost:3000`.

## Build & Start

```bash
npm run build
npm start
```
