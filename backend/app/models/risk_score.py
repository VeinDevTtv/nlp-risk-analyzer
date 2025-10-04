from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    ticker_id = Column(Integer, ForeignKey("tickers.id", ondelete="CASCADE"), nullable=False, index=True)
    headline_id = Column(Integer, ForeignKey("headlines.id", ondelete="SET NULL"), nullable=True, index=True)

    model = Column(String(64), nullable=False, default="finbert")
    sentiment = Column(Float, nullable=True)
    urgency = Column(Float, nullable=True)
    volatility = Column(Float, nullable=True)
    composite = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    ticker = relationship("Ticker", back_populates="risk_scores")


