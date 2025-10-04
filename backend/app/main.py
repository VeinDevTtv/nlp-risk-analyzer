from fastapi import FastAPI
from app.api.v1.status import router as v1_status_router

app = FastAPI(title="NLP Risk Analyzer API")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Mount versioned API routers
app.include_router(v1_status_router)

# OpenAPI is automatically mounted at /docs and /openapi.json by FastAPI
