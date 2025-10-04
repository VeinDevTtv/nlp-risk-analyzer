from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Ticker(Base):
    __tablename__ = "tickers"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    sector = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    mentions = relationship("Mention", back_populates="ticker", cascade="all, delete-orphan")
    risk_scores = relationship("RiskScore", back_populates="ticker", cascade="all, delete-orphan")


