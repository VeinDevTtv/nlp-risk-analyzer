from fastapi import FastAPI
from app.api.v1 import api_v1_router

app = FastAPI(title="NLP Risk Analyzer API")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Mount versioned API routers
app.include_router(api_v1_router)

# OpenAPI is automatically mounted at /docs and /openapi.json by FastAPI
