from typing import Any, Dict, Iterable, List, Optional, Tuple

from difflib import get_close_matches


try:
    import spacy  # type: ignore
except Exception:  # pragma: no cover - optional in tests
    spacy = None  # type: ignore

try:
    from transformers import pipeline  # type: ignore
except Exception:  # pragma: no cover - optional in tests
    pipeline = None  # type: ignore

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.headline import Headline
from app.models.mention import Mention
from app.models.risk_score import RiskScore
from app.models.ticker import Ticker


_nlp_model = None
_sentiment_pipeline = None


def _get_spacy_model():
    global _nlp_model
    if _nlp_model is not None:
        return _nlp_model

    if spacy is None:
        _nlp_model = None
        return _nlp_model

    # Prefer a small English model; fall back to blank with NER disabled
    try:
        _nlp_model = spacy.load("en_core_web_sm")
    except Exception:  # pragma: no cover - model may not be installed in CI
        _nlp_model = spacy.blank("en")
    return _nlp_model


def _get_sentiment_pipeline():
    global _sentiment_pipeline
    if _sentiment_pipeline is not None:
        return _sentiment_pipeline

    if pipeline is None:
        _sentiment_pipeline = None
        return _sentiment_pipeline

    # Try FinBERT first, else fallback to robust general model
    model_names = [
        "ProsusAI/finbert",
        "yiyanghkust/finbert-tone",
        "cardiffnlp/twitter-roberta-base-sentiment-latest",
        "distilbert-base-uncased-finetuned-sst-2-english",
    ]
    for name in model_names:
        try:
            _sentiment_pipeline = pipeline("sentiment-analysis", model=name, top_k=None)
            break
        except Exception:  # pragma: no cover - model download may fail
            _sentiment_pipeline = None
            continue
    return _sentiment_pipeline


def detect_entities(text: str) -> List[str]:
    """Return candidate company names/tickers using spaCy NER.

    Entities of types ORG and PRODUCT are considered; also pull in uppercase tokens as potential tickers.
    """
    if not text:
        return []

    nlp = _get_spacy_model()
    candidates: List[str] = []

    if nlp is not None and hasattr(nlp, "__call__"):
        doc = nlp(text)
        for ent in getattr(doc, "ents", []):
            if ent.label_ in {"ORG", "PRODUCT"}:
                val = ent.text.strip()
                if val and val not in candidates:
                    candidates.append(val)

        # Heuristic: uppercase tokens length 1..5 could be tickers
        for token in getattr(doc, "tokens", []) or doc:
            t = str(token).strip()
            if t.isupper() and 1 <= len(t) <= 5 and t.isalpha():
                if t not in candidates:
                    candidates.append(t)
    else:
        # Very lightweight fallback heuristic
        tokens = [t for t in text.split() if t.isalpha()]
        for t in tokens:
            if t.isupper() and 1 <= len(t) <= 5:
                if t not in candidates:
                    candidates.append(t)

    return candidates


def map_entities_to_tickers(db: Session, entities: Iterable[str]) -> List[Ticker]:
    """Map entity strings to `Ticker` rows using exact/symbol match and fuzzy fallback.

    - Exact match on `Ticker.symbol`
    - Case-insensitive exact match on `Ticker.name`
    - Fuzzy match via difflib against all known names if no exact match
    """
    cleaned = [e.strip() for e in entities if e and e.strip()]
    if not cleaned:
        return []

    # Load all tickers once for matching
    tickers: List[Ticker] = list(db.execute(select(Ticker)).scalars().all())
    symbol_to_ticker = {t.symbol.upper(): t for t in tickers if t.symbol}
    name_to_ticker_lower = {t.name.lower(): t for t in tickers if t.name}
    all_names_lower = list(name_to_ticker_lower.keys())

    mapped: List[Ticker] = []
    added_ids: set[int] = set()

    for e in cleaned:
        # symbol exact
        sym = e.upper()
        if sym in symbol_to_ticker:
            t = symbol_to_ticker[sym]
            if t.id not in added_ids:
                mapped.append(t)
                added_ids.add(t.id)
            continue

        # name exact (case insensitive)
        lower = e.lower()
        if lower in name_to_ticker_lower:
            t = name_to_ticker_lower[lower]
            if t.id not in added_ids:
                mapped.append(t)
                added_ids.add(t.id)
            continue

        # fuzzy fallback against names only
        if all_names_lower:
            matches = get_close_matches(lower, all_names_lower, n=1, cutoff=0.85)
            if matches:
                t = name_to_ticker_lower[matches[0]]
                if t.id not in added_ids:
                    mapped.append(t)
                    added_ids.add(t.id)

    return mapped


def sentiment_score(text: str) -> Optional[float]:
    """Return sentiment in [-1, 1]. If model unavailable, return 0.

    For models that return labels like POSITIVE/NEGATIVE with scores in [0,1], map to [-1,1].
    """
    if not text:
        return 0.0

    pipe = _get_sentiment_pipeline()
    if pipe is None:
        return 0.0

    try:
        result = pipe(text)
        if isinstance(result, list) and result:
            item = result[0]
            # transformers pipelines may return dict with label and score
            label = str(item.get("label", "")).lower()
            score = float(item.get("score", 0.0))
            # Normalize
            if "positive" in label:
                return max(-1.0, min(1.0, score))
            if "negative" in label:
                return max(-1.0, min(1.0, -score))
            if "neutral" in label:
                return 0.0
        return 0.0
    except Exception:  # pragma: no cover - model may fail
        return 0.0


def urgency_score(text: str) -> float:
    """Compute urgency score based on weighted keyword matches in text.

    Score in [0, 1].
    """
    if not text:
        return 0.0

    keywords: List[Tuple[str, float]] = [
        ("breaking", 1.0),
        ("urgent", 1.0),
        ("plunges", 0.8),
        ("soars", 0.8),
        ("downgrade", 0.6),
        ("upgrade", 0.6),
        ("halts", 0.7),
        ("bankruptcy", 1.0),
        ("investigation", 0.6),
        ("guidance cut", 0.8),
        ("profit warning", 0.9),
    ]

    text_l = text.lower()
    total_weight = sum(w for _, w in keywords)
    matched = 0.0
    for k, w in keywords:
        if k in text_l:
            matched += w

    score = matched / total_weight if total_weight else 0.0
    return float(max(0.0, min(1.0, score)))


def process_headline(db: Session, headline_id: int) -> Dict[str, Any]:
    """Process a headline by id: detect entities, map to tickers, compute scores, and write DB records.

    Returns a summary dict with tickers and scores.
    """
    headline = db.execute(select(Headline).where(Headline.id == headline_id)).scalar_one_or_none()
    if headline is None:
        raise ValueError("headline not found")

    entities = detect_entities(headline.title or "")
    tickers = map_entities_to_tickers(db, entities)

    sent = sentiment_score(headline.title or "")
    urg = urgency_score(headline.title or "")

    # Upsert mentions for each ticker
    created_mentions = 0
    for t in tickers:
        mention = Mention(
            headline_id=headline.id,
            ticker_id=t.id,
            context=headline.title[:512] if headline.title else None,
            relevance=1.0,
        )
        db.add(mention)
        created_mentions += 1

        # Persist a risk score row per ticker-headline
        rs = RiskScore(
            ticker_id=t.id,
            headline_id=headline.id,
            model="finbert",
            sentiment=float(sent) if sent is not None else None,
            urgency=float(urg),
            volatility=None,
            composite=None,
        )
        db.add(rs)

    db.commit()

    return {
        "headline_id": headline.id,
        "tickers": [t.symbol for t in tickers],
        "sentiment": sent,
        "urgency": urg,
        "mentions_created": created_mentions,
    }


