from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Mention(Base):
    __tablename__ = "mentions"

    id = Column(Integer, primary_key=True, index=True)
    headline_id = Column(Integer, ForeignKey("headlines.id", ondelete="CASCADE"), nullable=False, index=True)
    ticker_id = Column(Integer, ForeignKey("tickers.id", ondelete="CASCADE"), nullable=False, index=True)
    context = Column(String(512), nullable=True)
    relevance = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    headline = relationship("Headline", back_populates="mentions")
    ticker = relationship("Ticker", back_populates="mentions")


