import os
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# Ensure backend package importable and test DB configured
CURRENT_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.models.ticker import Ticker  # noqa: E402
from app.models.risk_score import RiskScore  # noqa: E402
from app.analysis.backtest import compute_metrics, fetch_risk_timeseries  # noqa: E402


def setup_function(_: object) -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def _make_business_days(n: int, start: datetime | None = None) -> pd.DatetimeIndex:
    start = start or datetime(2025, 1, 1)
    return pd.bdate_range(start=start, periods=n)


def test_compute_metrics_synthetic_directionality() -> None:
    # Build synthetic price series with controlled next-day returns
    n = 12
    dates = _make_business_days(n)
    next_day_returns = np.array([-0.05, 0.02, -0.03, 0.01, -0.04, 0.015, 0.0, -0.02, 0.03, -0.01, 0.02])
    assert len(next_day_returns) == n - 1

    close = [100.0]
    for r in next_day_returns:
        close.append(close[-1] * (1.0 + float(r)))
    prices = pd.DataFrame({"Close": close}, index=dates)

    # Risk higher on days preceding negative returns; create multiple max-risk ties
    risk_values = []
    for r in next_day_returns:
        if r < 0:
            risk_values.append(1.0)  # top risk
        else:
            risk_values.append(0.2)
    # add value for the last day (no next return), set to median
    risk_values.append(0.5)
    daily_risk = pd.Series(risk_values, index=dates)

    results = compute_metrics(prices, daily_risk)

    assert results.count_observations == n - 1
    assert results.pearson_corr is not None
    # Correlation should be negative: higher risk associates with more negative next-day returns
    assert results.pearson_corr < 0.0

    # With many top-tied risk days, 90th percentile should select multiple negatives
    assert results.auc_thresholded is None or results.auc_thresholded >= 0.5

    # Average next-day return after top-decile risk should be negative
    assert results.avg_return_top_decile is None or results.avg_return_top_decile < 0.0


def test_fetch_risk_timeseries_daily_mean_aggregation() -> None:
    # Insert ticker and multiple risk rows per day; expect daily mean
    with SessionLocal() as db:
        t = Ticker(symbol="TEST", name="Test Corp")
        db.add(t)
        db.commit()

        base_date = datetime(2025, 1, 2)
        # Day 1: two entries 0.4 and 0.6 -> mean 0.5
        db.add_all([
            RiskScore(ticker_id=t.id, composite=0.4, created_at=base_date + timedelta(hours=1), model="x"),
            RiskScore(ticker_id=t.id, composite=0.6, created_at=base_date + timedelta(hours=5), model="x"),
        ])
        # Day 2: one entry 0.9
        db.add(
            RiskScore(ticker_id=t.id, composite=0.9, created_at=base_date + timedelta(days=1, hours=3), model="x")
        )
        db.commit()

    series = fetch_risk_timeseries("TEST", base_date.date(), (base_date + timedelta(days=2)).date())
    series = series.sort_index()

    assert len(series) == 2
    # Compare dates normalized
    day1 = pd.to_datetime(base_date).normalize()
    day2 = pd.to_datetime(base_date + timedelta(days=1)).normalize()
    assert abs(float(series.loc[day1]) - 0.5) < 1e-9
    assert abs(float(series.loc[day2]) - 0.9) < 1e-9


