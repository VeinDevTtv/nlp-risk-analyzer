import os
import sys
import types

# Ensure backend package is importable
CURRENT_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Configure test database BEFORE importing session
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

import pytest  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.models.ticker import Ticker  # noqa: E402
from app.models.headline import Headline  # noqa: E402
from app.models.mention import Mention  # noqa: E402
from app.models.risk_score import RiskScore  # noqa: E402
from app.nlp import processor as p  # noqa: E402


def setup_function(_: object) -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def test_detect_entities_fallback_uppercase() -> None:
    text = "BREAKING: AAPL plunges as Apple faces investigation"
    ents = p.detect_entities(text)
    assert "AAPL" in ents


def test_map_entities_to_tickers_exact_and_fuzzy() -> None:
    with SessionLocal() as db:
        aapl = Ticker(symbol="AAPL", name="Apple Inc.")
        goog = Ticker(symbol="GOOGL", name="Alphabet Inc.")
        db.add_all([aapl, goog])
        db.commit()

        mapped1 = p.map_entities_to_tickers(db, ["AAPL"])  # symbol exact
        assert len(mapped1) == 1 and mapped1[0].symbol == "AAPL"

        mapped2 = p.map_entities_to_tickers(db, ["Apple Inc"])  # name nearly exact
        assert any(t.symbol == "AAPL" for t in mapped2)


def test_sentiment_and_urgency_with_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    # Force a trivial sentiment pipeline that returns POSITIVE with score 0.7
    class FakePipe:
        def __call__(self, text):
            return [{"label": "POSITIVE", "score": 0.7}]

    monkeypatch.setattr(p, "_sentiment_pipeline", FakePipe())

    s = p.sentiment_score("Shares soar on strong guidance")
    assert 0.5 < s <= 1.0

    u = p.urgency_score("BREAKING: profit warning issued; trading halts")
    assert 0.0 <= u <= 1.0
    assert u > 0.0


def test_process_headline_creates_mentions_and_risk_scores(monkeypatch: pytest.MonkeyPatch) -> None:
    # Use minimal/fake NLP to keep test fast
    monkeypatch.setattr(p, "detect_entities", lambda text: ["AAPL"])  # direct ticker symbol
    monkeypatch.setattr(p, "sentiment_score", lambda text: -0.4)
    monkeypatch.setattr(p, "urgency_score", lambda text: 0.6)

    with SessionLocal() as db:
        aapl = Ticker(symbol="AAPL", name="Apple Inc.")
        db.add(aapl)
        db.commit()

        h = Headline(title="AAPL plunges after guidance cut", url="https://example.com/x")
        db.add(h)
        db.commit()

        summary = p.process_headline(db, h.id)

        assert summary["headline_id"] == h.id
        assert summary["tickers"] == ["AAPL"]
        assert summary["sentiment"] == -0.4
        assert summary["urgency"] == 0.6

        mentions = db.query(Mention).all()
        assert len(mentions) == 1
        assert mentions[0].ticker_id == aapl.id

        scores = db.query(RiskScore).all()
        assert len(scores) == 1
        assert scores[0].ticker_id == aapl.id and scores[0].headline_id == h.id
        assert scores[0].sentiment == -0.4 and scores[0].urgency == 0.6


