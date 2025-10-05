from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import api_v1_router

app = FastAPI(title="NLP Risk Analyzer API")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


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
