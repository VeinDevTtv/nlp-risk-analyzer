from typing import Dict, Optional


DEFAULT_WEIGHTS = {
    "sentiment": 0.6,   # sentiment in [-1, 1] mapped to [0, 100]
    "urgency": 0.3,     # urgency in [0, 1] mapped to [0, 100]
    "volatility": 0.1,  # volatility in [0, 1] mapped to [0, 100]
}


def _clamp(value: float, min_value: float, max_value: float) -> float:
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value


def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(float(w) for w in weights.values()) or 1.0
    return {k: float(v) / total for k, v in weights.items()}


def compute_risk_score(
    sentiment_score: Optional[float],
    urgency: Optional[float],
    volatility: Optional[float],
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, object]:
    """Compute composite risk and components.

    Inputs:
      - sentiment_score: float in [-1, 1] (negative means riskier). If None, treated as 0.
      - urgency: float in [0, 1]. If None, treated as 0.
      - volatility: float in [0, 1]. If None, treated as 0.
      - weights: dict with keys 'sentiment', 'urgency', 'volatility'. If missing, defaults used.

    Returns dict:
      {
        "risk_percent": float (0..100, rounded to 2 decimals),
        "components": {
            "sentiment": float (0..100),
            "urgency": float (0..100),
            "volatility": float (0..100)
        }
      }
    """
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update({k: float(v) for k, v in weights.items() if k in w})
    w = _normalize_weights(w)

    # Clamp inputs and map to 0..100 component scales where higher = more risk
    s_raw = 0.0 if sentiment_score is None else _clamp(float(sentiment_score), -1.0, 1.0)
    # Convert sentiment in [-1,1] to risk percent 0..100 with -1 => 100 (risk), +1 => 0
    sentiment_risk = (1.0 - s_raw) * 50.0

    u_raw = 0.0 if urgency is None else _clamp(float(urgency), 0.0, 1.0)
    urgency_risk = u_raw * 100.0

    v_raw = 0.0 if volatility is None else _clamp(float(volatility), 0.0, 1.0)
    volatility_risk = v_raw * 100.0

    components = {
        "sentiment": sentiment_risk,
        "urgency": urgency_risk,
        "volatility": volatility_risk,
    }

    risk_percent = (
        components["sentiment"] * w["sentiment"]
        + components["urgency"] * w["urgency"]
        + components["volatility"] * w["volatility"]
    )

    # Precision to two decimals for the composite
    return {
        "risk_percent": round(float(risk_percent), 2),
        "components": components,
    }


