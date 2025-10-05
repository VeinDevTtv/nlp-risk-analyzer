## Security Guidelines

This document outlines how to handle secrets, rotate credentials, rate‑limit ingestion to respect third‑party APIs, and comply with data‑source Terms of Service (TOS).

### 1) Secret management and key rotation

- Do not commit secrets/keys/tokens to the repository. Keep secrets in environment variables and external secret managers.
- Use `.env` files locally (never commit them) and provider secrets in CI/CD (e.g., GitHub Actions, Vercel, Render, Railway).
- Ensure `.gitignore` excludes `.env*` and any secret-bearing files.

Rotation policy and procedure:
1. Create a new key in the provider console.
2. Add the new key to secret storage for all environments (local, staging, prod) under a new variable name or safely update the existing one.
3. Deploy/restart services using the new key.
4. Validate functionality and logs for errors.
5. Revoke the old key and record rotation time and owner.

Operational recommendations:
- Prefer short‑lived tokens where possible; set expirations and reminders to rotate.
- Scope keys to least privilege.
- Use distinct keys per environment.
- Log key usage metadata (not the key itself) to aid audits.

Leak response:
1. Immediately revoke exposed keys.
2. Rotate keys following the steps above.
3. Invalidate any cached credentials, restart affected services, and review logs for misuse.
4. File an incident with timeline, blast radius, and corrective actions.

### 2) Respecting API rate limits and fair use

Always adhere to each provider’s published rate limits and fair‑use policies. Ingestion code (e.g., `backend/app/ingest/news_fetcher.py`) and scheduling (e.g., `backend/app/workers/scheduler.py`) must enforce conservative limits.

Implementation guidelines:
- Centralize rate‑limit configs via environment variables (e.g., `NEWSAPI_REQUESTS_PER_MINUTE`).
- Use backoff with jitter (exponential or decorrelated) on 429/5xx.
- Cache responses where permitted to reduce repeated calls.
- Respect per‑key and per‑IP quotas; keep concurrency low.
- Add guards for daily/monthly caps to avoid overage.
- Prefer scheduled batch windows over tight polling loops.

Example environment variables (illustrative):

```
# NewsAPI example
NEWSAPI_REQUESTS_PER_MINUTE=20
NEWSAPI_DAILY_CAP=900

# Global ingestion safeguards
INGEST_MAX_CONCURRENCY=2
INGEST_BACKOFF_BASE_SECONDS=2
INGEST_BACKOFF_MAX_SECONDS=60
```

### 3) Terms of Service (TOS) compliance

You must read and comply with TOS for all data sources. The notes below are non‑exhaustive and may change; always consult official terms.

| Source | Key TOS Notes (non‑exhaustive) | TOS Link |
| --- | --- | --- |
| NewsAPI | Non‑commercial/attribution rules vary by plan; do not store full content beyond allowed retention; respect rate limits; link back to original sources. | https://newsapi.org/terms |
| Other sources you add | Verify allowed caching, redistribution, and commercial use; follow attribution requirements; respect robots.txt and API usage limits. | Refer to provider site |

If a provider forbids certain storage or redistribution, configure ingestion to store only permitted fields (e.g., metadata, titles, URLs) and avoid persisting full articles if not allowed.

### 4) Data minimization and PII

- Do not ingest or store personally identifiable information (PII) unless strictly necessary.
- For analytics, use aggregated or anonymized metrics.

### 5) Vulnerability reporting

If you discover a security issue, please open a private security report (do not file a public issue). Provide steps to reproduce, impact assessment, and environment details.


