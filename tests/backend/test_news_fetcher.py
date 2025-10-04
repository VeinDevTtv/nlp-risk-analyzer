import os
import sys
import types
import asyncio
import datetime as dt

# Ensure backend package is importable
CURRENT_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Configure test database BEFORE importing session
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

import aiohttp  # noqa: E402
import feedparser  # noqa: E402
import pytest  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.ingest.news_fetcher import fetch_from_newsapi, fetch_from_rss, save_headlines  # noqa: E402
from app.models.headline import Headline  # noqa: E402


def setup_function(_: object) -> None:
    # Recreate schema for each test
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@pytest.mark.asyncio
async def test_newsapi_fetch_and_save(monkeypatch: pytest.MonkeyPatch) -> None:
    os.environ["NEWSAPI_KEY"] = "test-key"

    class FakeResponse:
        def __init__(self, data: dict, status: int = 200) -> None:
            self._data = data
            self.status = status

        async def json(self) -> dict:
            return self._data

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeSession:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def get(self, url, params=None, headers=None):
            data = {
                "articles": [
                    {
                        "title": "AAPL plunges after earnings miss",
                        "url": "https://example.com/1",
                        "source": {"name": "NewsAPI"},
                        "publishedAt": "2025-10-02T12:00:00Z",
                    },
                    {
                        # duplicate by text (hash)
                        "title": "AAPL plunges after earnings miss",
                        "url": "https://example.com/2",
                        "source": {"name": "NewsAPI"},
                        "publishedAt": "2025-10-02T12:05:00Z",
                    },
                ]
            }
            return FakeResponse(data, 200)

    monkeypatch.setattr(aiohttp, "ClientSession", FakeSession)

    items = await fetch_from_newsapi()
    assert len(items) == 2
    with SessionLocal() as db:
        inserted = save_headlines(db, items)
        assert inserted == 1

        # Insert again should yield 0 (all duplicates)
        inserted2 = save_headlines(db, items)
        assert inserted2 == 0

        # Verify DB state
        rows = db.query(Headline).all()
        assert len(rows) == 1
        assert rows[0].title == "AAPL plunges after earnings miss"


def test_rss_fetch_and_save(monkeypatch: pytest.MonkeyPatch) -> None:
    class ParsedFeed:
        def __init__(self):
            self.feed = types.SimpleNamespace(title="Reuters")
            self.entries = [
                {
                    "title": "Fed signals possible rate cut",
                    "link": "https://reuters.example.com/a",
                    "published": "Thu, 02 Oct 2025 12:00:00 GMT",
                },
                {
                    # duplicate by URL
                    "title": "Fed signals possible rate cut (update)",
                    "link": "https://reuters.example.com/a",
                    "published": "Thu, 02 Oct 2025 12:05:00 GMT",
                },
            ]

    def fake_parse(url: str):
        return ParsedFeed()

    monkeypatch.setattr(feedparser, "parse", fake_parse)

    items = fetch_from_rss(["https://reuters.example.com/rss"])
    assert len(items) == 2

    with SessionLocal() as db:
        inserted = save_headlines(db, items)
        assert inserted == 1

        rows = db.query(Headline).order_by(Headline.id).all()
        assert len(rows) == 1
        assert rows[0].source == "Reuters"
        assert rows[0].url == "https://reuters.example.com/a"
        assert rows[0].title.startswith("Fed signals possible rate cut")


