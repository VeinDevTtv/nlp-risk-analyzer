import os
import sys

import pytest
from httpx import AsyncClient


# Ensure backend package is importable and DB is in-memory for tests
CURRENT_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


def setup_function(_: object) -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@pytest.mark.asyncio
async def test_analyze_endpoint_basic_fields() -> None:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {"text": "BREAKING: AAPL plunges after earnings miss"}
        resp = await ac.post("/v1/analyze", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        # Required fields
        for key in [
            "text",
            "entities",
            "sentiment",
            "urgency",
            "volatility",
            "risk_percent",
        ]:
            assert key in data

        assert isinstance(data["text"], str) and len(data["text"]) > 0
        assert isinstance(data["entities"], list)
        # Entities items shape
        for e in data["entities"]:
            assert "name" in e
            assert "ticker" in e  # may be None

        # Ranges
        assert -1.0 <= float(data["sentiment"]) <= 1.0
        assert 0.0 <= float(data["urgency"]) <= 1.0
        assert 0.0 <= float(data["volatility"]) <= 1.0
        assert 0.0 <= float(data["risk_percent"]) <= 100.0


@pytest.mark.asyncio
async def test_analyze_endpoint_handles_empty_entities_gracefully() -> None:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {"text": "Market updates throughout the day"}
        resp = await ac.post("/v1/analyze", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert isinstance(data["entities"], list)
        # Even if no uppercase tickers, response must include fields in range
        assert -1.0 <= float(data["sentiment"]) <= 1.0
        assert 0.0 <= float(data["urgency"]) <= 1.0
        assert 0.0 <= float(data["volatility"]) <= 1.0
        assert 0.0 <= float(data["risk_percent"]) <= 100.0


