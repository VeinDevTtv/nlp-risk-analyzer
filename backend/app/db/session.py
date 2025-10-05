import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base  # noqa: F401  (imported for potential metadata usage)


# Load environment variables from a .env file if present
load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is required (example: postgresql+psycopg2://user:pass@host:5432/dbname)"
    )

# Configure engine with SQLite-specific settings for tests and thread safety
_url = make_url(DATABASE_URL)
_engine_kwargs = {"pool_pre_ping": True, "future": True}

if _url.drivername.startswith("sqlite"):
    # Allow usage across threads (FastAPI may run deps in threadpool)
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
    # For in-memory SQLite, reuse the same connection across the app/tests
    # so that the schema persists and cross-thread access works.
    if _url.database in (None, "", ":memory:"):
        _engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, **_engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


