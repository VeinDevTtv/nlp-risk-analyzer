from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Headline(Base):
    __tablename__ = "headlines"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(255), nullable=True)
    url = Column(Text, nullable=True)
    title = Column(Text, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    mentions = relationship("Mention", back_populates="headline", cascade="all, delete-orphan")


