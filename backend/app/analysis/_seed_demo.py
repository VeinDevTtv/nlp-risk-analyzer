from __future__ import annotations

from datetime import datetime, timedelta

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.ticker import Ticker
from app.models.risk_score import RiskScore


def main() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        aapl = Ticker(symbol="AAPL", name="Apple Inc.")
        db.add(aapl)
        db.commit()
        db.refresh(aapl)

        start = datetime(2024, 1, 2)
        # Insert 15 days of synthetic risk values in Jan 2024
        for i in range(15):
            ts = start + timedelta(days=i)
            # Cycle risk between 0.2..0.4..0.6 to create variation
            composite = 0.2 + 0.05 * (i % 5)
            db.add(
                RiskScore(
                    ticker_id=aapl.id,
                    composite=composite,
                    created_at=ts,
                    model="synthetic",
                )
            )
        db.commit()

    print("Seeded synthetic risk data for AAPL (Jan 2024).")


if __name__ == "__main__":
    main()


