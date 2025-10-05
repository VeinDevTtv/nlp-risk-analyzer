from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.metrics import roc_auc_score

from app.db.session import SessionLocal
from app.models.risk_score import RiskScore
from app.models.ticker import Ticker

try:
    import yfinance as yf  # type: ignore
except Exception:  # pragma: no cover - optional dependency in tests
    yf = None


DateLike = str


@dataclass
class BacktestResults:
    pearson_corr: Optional[float]
    auc_thresholded: Optional[float]
    avg_return_top_decile: Optional[float]
    count_observations: int


def _ensure_datetime(date_str: DateLike) -> datetime:
    if isinstance(date_str, datetime):
        return date_str
    return datetime.fromisoformat(str(date_str))


def fetch_price_history(symbol: str, start: DateLike, end: DateLike) -> pd.DataFrame:
    """Fetch historical adjusted close prices using yfinance.

    Returns a DataFrame indexed by date with a 'Close' column.
    """
    if yf is None:
        raise RuntimeError("yfinance is not installed. Please add it to requirements and install.")

    start_dt = _ensure_datetime(start)
    end_dt = _ensure_datetime(end)

    df = yf.download(tickers=symbol, start=start_dt, end=end_dt, progress=False, auto_adjust=True)
    if df is None or df.empty:
        raise RuntimeError(f"No price data returned for {symbol} between {start} and {end}")

    # Standardize columns
    if "Adj Close" in df.columns and "Close" not in df.columns:
        df = df.rename(columns={"Adj Close": "Close"})
    if "Close" not in df.columns:
        raise RuntimeError("Downloaded data does not contain 'Close' or 'Adj Close' columns")

    df = df[["Close"]].copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df = df.sort_index()
    return df


def fetch_risk_timeseries(symbol: str, start: DateLike, end: DateLike) -> pd.Series:
    """Fetch risk scores from the DB and aggregate to daily mean per date.

    Returns a Series indexed by date with daily risk (composite) values.
    """
    start_dt = _ensure_datetime(start)
    end_dt = _ensure_datetime(end)

    with SessionLocal() as db:
        ticker: Optional[Ticker] = db.query(Ticker).filter(Ticker.symbol == symbol).first()
        if ticker is None:
            raise RuntimeError(f"Ticker '{symbol}' not found in database")

        q = (
            db.query(RiskScore.created_at, RiskScore.composite)
            .filter(RiskScore.ticker_id == ticker.id)
            .filter(RiskScore.created_at >= start_dt)
            .filter(RiskScore.created_at <= end_dt)
            .order_by(RiskScore.created_at.asc())
        )
        rows = q.all()

    if not rows:
        raise RuntimeError("No risk scores found for given range")

    df = pd.DataFrame(rows, columns=["created_at", "risk"]).dropna()
    if df.empty:
        raise RuntimeError("Risk scores are empty after dropping NaNs")

    df["date"] = pd.to_datetime(df["created_at"]).dt.tz_localize(None).dt.normalize()
    daily = df.groupby("date")["risk"].mean().sort_index()
    return daily


def _align_risk_and_next_returns(prices: pd.DataFrame, daily_risk: pd.Series) -> Tuple[pd.Series, pd.Series, pd.DataFrame]:
    prices = prices.copy()
    prices.index = pd.to_datetime(prices.index).tz_localize(None)
    prices = prices.sort_index()

    # Compute daily simple returns labeled at t (return from t-1 -> t)
    daily_returns = prices["Close"].pct_change()
    # Align to risk at t by shifting next-day returns back to t index
    next_day_returns = daily_returns.shift(-1)

    # Align risk (daily) to trading calendar; forward-fill within the same day is not needed
    risk_daily = daily_risk.copy()
    risk_daily.index = pd.to_datetime(risk_daily.index).tz_localize(None)
    risk_daily = risk_daily.sort_index()

    # Join on date index
    df = pd.DataFrame({"risk": risk_daily}).join(next_day_returns.to_frame("next_ret"), how="inner")
    df = df.dropna()
    return df["risk"], df["next_ret"], df


def compute_metrics(prices: pd.DataFrame, daily_risk: pd.Series) -> BacktestResults:
    risk, next_ret, df = _align_risk_and_next_returns(prices, daily_risk)
    n = int(len(df))
    if n < 3:
        return BacktestResults(
            pearson_corr=None,
            auc_thresholded=None,
            avg_return_top_decile=None,
            count_observations=n,
        )

    # Pearson correlation between risk_t and return_{t+1}
    try:
        pearson = float(risk.corr(next_ret))
    except Exception:
        pearson = None

    # Classification AUC predicting negative next-day returns using thresholded risk
    try:
        threshold = float(np.nanpercentile(risk.values, 90.0))
        risk_high = (risk.values >= threshold).astype(int)
        y_true = (next_ret.values < 0.0).astype(int)
        # roc_auc_score requires both classes present
        if len(np.unique(y_true)) < 2 or len(np.unique(risk_high)) < 2:
            auc_thr = None
        else:
            auc_thr = float(roc_auc_score(y_true, risk_high))
    except Exception:
        auc_thr = None

    # Average next-day return after top-decile risk events
    try:
        mask_top_decile = risk.values >= threshold  # reuse threshold
        if mask_top_decile.any():
            avg_top = float(np.nanmean(next_ret.values[mask_top_decile]))
        else:
            avg_top = None
    except Exception:
        avg_top = None

    return BacktestResults(
        pearson_corr=pearson,
        auc_thresholded=auc_thr,
        avg_return_top_decile=avg_top,
        count_observations=n,
    )


def _ensure_outdir(outdir: str) -> str:
    os.makedirs(outdir, exist_ok=True)
    return outdir


def generate_report(
    symbol: str,
    start: DateLike,
    end: DateLike,
    prices: pd.DataFrame,
    daily_risk: pd.Series,
    results: BacktestResults,
    outdir: str,
) -> Dict[str, str]:
    outdir = _ensure_outdir(outdir)
    start_str = _ensure_datetime(start).date().isoformat()
    end_str = _ensure_datetime(end).date().isoformat()

    # Plots
    # 1) Price and risk (twin axes)
    fig, ax1 = plt.subplots(figsize=(9, 4))
    ax2 = ax1.twinx()
    ax1.plot(prices.index, prices["Close"], color="#1f77b4", label="Close")
    ax2.plot(daily_risk.index, daily_risk.values, color="#d62728", alpha=0.6, label="Risk")
    ax1.set_title(f"{symbol} Price and Risk ({start_str} to {end_str})")
    ax1.set_ylabel("Close")
    ax2.set_ylabel("Risk")
    fig.tight_layout()
    price_risk_png = os.path.join(outdir, f"{symbol}_{start_str}_{end_str}_price_risk.png")
    fig.savefig(price_risk_png, dpi=120)
    plt.close(fig)

    # 2) Scatter risk vs next-day return
    _, _, aligned = _align_risk_and_next_returns(prices, daily_risk)
    fig2, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(aligned["risk"], aligned["next_ret"], s=18, alpha=0.7)
    ax.axhline(0.0, color="gray", linewidth=1)
    ax.set_xlabel("Risk (t)")
    ax.set_ylabel("Return (t+1)")
    ax.set_title("Risk vs Next-Day Return")
    fig2.tight_layout()
    scatter_png = os.path.join(outdir, f"{symbol}_{start_str}_{end_str}_scatter.png")
    fig2.savefig(scatter_png, dpi=120)
    plt.close(fig2)

    # CSV metrics
    metrics_csv = os.path.join(outdir, f"{symbol}_{start_str}_{end_str}_metrics.csv")
    metrics_df = pd.DataFrame(
        [
            {
                "symbol": symbol,
                "start": start_str,
                "end": end_str,
                "pearson_corr": results.pearson_corr,
                "auc_thresholded": results.auc_thresholded,
                "avg_return_top_decile": results.avg_return_top_decile,
                "n": results.count_observations,
            }
        ]
    )
    metrics_df.to_csv(metrics_csv, index=False)

    # HTML report (lightweight)
    html_path = os.path.join(outdir, f"{symbol}_{start_str}_{end_str}_report.html")
    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <title>Backtest Report - {symbol}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; }}
    .metric {{ margin: 4px 0; }}
    img {{ max-width: 100%; height: auto; }}
  </style>
  </head>
<body>
  <h2>Backtest Report - {symbol}</h2>
  <div class=\"metric\">Date range: <b>{start_str}</b> to <b>{end_str}</b></div>
  <div class=\"metric\">Observations (days): <b>{results.count_observations}</b></div>
  <div class=\"metric\">Pearson corr (risk_t vs return_t+1): <b>{results.pearson_corr if results.pearson_corr is not None else 'NA'}</b></div>
  <div class=\"metric\">AUC (thresholded risk → negative return): <b>{results.auc_thresholded if results.auc_thresholded is not None else 'NA'}</b></div>
  <div class=\"metric\">Avg next-day return after top-decile risk: <b>{results.avg_return_top_decile if results.avg_return_top_decile is not None else 'NA'}</b></div>

  <h3>Price and Risk</h3>
  <img src=\"{os.path.basename(price_risk_png)}\" alt=\"Price and Risk\" />

  <h3>Risk vs Next-Day Return</h3>
  <img src=\"{os.path.basename(scatter_png)}\" alt=\"Scatter\" />

  <h3>Metrics (CSV)</h3>
  <p>See <code>{os.path.basename(metrics_csv)}</code></p>
</body>
</html>
"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    return {
        "html": html_path,
        "csv": metrics_csv,
        "plot_price_risk": price_risk_png,
        "plot_scatter": scatter_png,
    }


def run_backtest(symbol: str, start: DateLike, end: DateLike, outdir: str) -> Dict[str, str]:
    prices = fetch_price_history(symbol, start, end)
    risk = fetch_risk_timeseries(symbol, start, end)
    results = compute_metrics(prices, risk)
    return generate_report(symbol, start, end, prices, risk, results, outdir)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Risk/Return backtester")
    p.add_argument("--symbol", required=True, help="Ticker symbol, e.g., AAPL")
    p.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    p.add_argument("--end", required=True, help="End date YYYY-MM-DD (exclusive)")
    p.add_argument("--outdir", default="backtest_reports", help="Output directory for report and plots")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    paths = run_backtest(args.symbol, args.start, args.end, args.outdir)
    print(f"Report written: {paths['html']}")


if __name__ == "__main__":
    main()


