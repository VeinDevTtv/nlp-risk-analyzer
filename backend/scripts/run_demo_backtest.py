import os
import sys
from datetime import datetime


def main() -> None:
    # Ensure backend is importable
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    # Use a local SQLite DB file
    db_path = os.path.join(backend_dir, "demo_backtest.db")
    db_url = "sqlite+pysqlite:///" + db_path.replace("\\", "/")
    os.environ["DATABASE_URL"] = db_url

    # Seed synthetic risk
    from app.analysis import _seed_demo  # type: ignore

    _seed_demo.main()

    # Try to run a backtest for Jan 2024
    from app.analysis import backtest  # type: ignore
    import pandas as pd
    import numpy as np

    symbol = "AAPL"
    start = "2024-01-01"
    end = "2024-02-01"
    outdir = os.path.join(backend_dir, "backtest_reports")

    # Try real prices; if unavailable, synthesize a simple price series
    try:
        prices = backtest.fetch_price_history(symbol, start, end)
    except Exception:
        # Synthesize business-day prices
        dates = pd.bdate_range(start=pd.to_datetime(start), end=pd.to_datetime(end) - pd.Timedelta(days=1))
        close = [100.0]
        rng = np.random.default_rng(42)
        rets = rng.normal(loc=0.0005, scale=0.01, size=len(dates) - 1)
        for r in rets:
            close.append(close[-1] * (1.0 + float(r)))
        prices = pd.DataFrame({"Close": close}, index=dates)

    daily_risk = backtest.fetch_risk_timeseries(symbol, start, end)
    results = backtest.compute_metrics(prices, daily_risk)
    paths = backtest.generate_report(symbol, start, end, prices, daily_risk, results, outdir)

    print("Backtest complete. Outputs:")
    for k, v in paths.items():
        print(f" - {k}: {v}")


if __name__ == "__main__":
    main()


