from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.nlp import processor
from app.utils.risk import compute_risk_score


class AnalyzeEntity(BaseModel):
    name: str
    ticker: Optional[str] = None


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1)


class AnalyzeResponse(BaseModel):
    text: str
    entities: List[AnalyzeEntity]
    sentiment: float
    urgency: float
    volatility: float
    risk_percent: float


router = APIRouter(prefix="/v1")


def _estimate_volatility(sentiment: float, urgency: float) -> float:
    """Lightweight volatility heuristic in [0,1].

    Combines magnitude of sentiment with urgency. Keeps computation local and fast.
    """
    s_mag = abs(float(sentiment))
    u_val = float(urgency)
    vol = 0.5 * s_mag + 0.5 * u_val
    if vol < 0.0:
        return 0.0
    if vol > 1.0:
        return 1.0
    return float(vol)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(payload: AnalyzeRequest, db: Session = Depends(get_db)) -> AnalyzeResponse:
    text = payload.text

    # Entity detection
    entity_strings = processor.detect_entities(text)

    # Try to map to known tickers via DB; fallback to simple heuristics if none
    entities: List[AnalyzeEntity] = []
    try:
        mapped = processor.map_entities_to_tickers(db, entity_strings)
        mapped_symbols = {t.symbol for t in mapped}
        for name in entity_strings:
            symbol: Optional[str] = None
            # Assign DB-mapped symbol if present (case-insensitive match against symbol set)
            if name.upper() in {s.upper() for s in mapped_symbols}:
                symbol = name.upper()
            elif name.isupper() and 1 <= len(name) <= 5 and name.isalpha():
                symbol = name
            entities.append(AnalyzeEntity(name=name, ticker=symbol))
    except Exception:
        # If DB unavailable or mapping fails, still return entities from heuristics
        for name in entity_strings:
            symbol = name if (name.isupper() and 1 <= len(name) <= 5 and name.isalpha()) else None
            entities.append(AnalyzeEntity(name=name, ticker=symbol))

    # Scores
    sentiment = float(processor.sentiment_score(text) or 0.0)
    urgency = float(processor.urgency_score(text))
    volatility = _estimate_volatility(sentiment, urgency)

    composite = compute_risk_score(
        sentiment_score=sentiment,
        urgency=urgency,
        volatility=volatility,
        weights=None,
    )

    return AnalyzeResponse(
        text=text,
        entities=entities,
        sentiment=sentiment,
        urgency=urgency,
        volatility=volatility,
        risk_percent=float(composite["risk_percent"]),
    )


