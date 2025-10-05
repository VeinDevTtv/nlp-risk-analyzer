import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import api_v1_router
from app.utils.logging import setup_logging

setup_logging()

# Sentry integration (optional)
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    try:
        import sentry_sdk  # type: ignore
        from sentry_sdk.integrations.fastapi import FastApiIntegration  # type: ignore
        from sentry_sdk.integrations.logging import LoggingIntegration  # type: ignore

        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR,
        )
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[FastApiIntegration(), sentry_logging],
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
        )
    except Exception:  # pragma: no cover
        pass

app = FastAPI(title="NLP Risk Analyzer API")


@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "NLP Risk Analyzer API. Visit /docs for OpenAPI and /health for status."}


# Mount versioned API routers
app.include_router(api_v1_router)

# OpenAPI is automatically mounted at /docs and /openapi.json by FastAPI

# Enable CORS for frontend consumption
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # consider restricting in production via env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics endpoint (optional)
try:
    from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, generate_latest  # type: ignore
    from fastapi import Response

    registry = CollectorRegistry()
    http_requests_total = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "path", "status"],
        registry=registry,
    )

    @app.middleware("http")
    async def metrics_middleware(request, call_next):  # type: ignore
        response = await call_next(request)
        try:
            http_requests_total.labels(request.method, request.url.path, str(response.status_code)).inc()
        except Exception:
            pass
        return response

    @app.get("/metrics")
    async def metrics() -> Response:  # type: ignore
        data = generate_latest(registry)
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)
except Exception:
    # If prometheus_client is not available, you can attach an exporter via infra (e.g., sidecar)
    pass
