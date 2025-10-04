import os
import logging
from typing import List

from dotenv import load_dotenv
from celery import Celery
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.headline import Headline
from app.models.mention import Mention
from app.models.risk_score import RiskScore
from app.ingest.news_fetcher import fetch_and_save
from app.nlp.processor import process_headline


load_dotenv()


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("celery-tasks")


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "nlp_risk_analyzer",
    broker=REDIS_URL,
    backend=REDIS_URL,
)


def _find_unprocessed_headline_ids(limit: int = 100) -> List[int]:
    with SessionLocal() as db:
        q = (
            select(Headline.id)
            .outerjoin(Mention, Mention.headline_id == Headline.id)
            .outerjoin(RiskScore, RiskScore.headline_id == Headline.id)
            .where(Mention.id == None, RiskScore.id == None)  # type: ignore
            .order_by(Headline.id.desc())
            .limit(limit)
        )
        rows = db.execute(q).scalars().all()
        return list(rows)


@celery_app.task(name="ingest.fetch_and_save")
def task_ingest() -> int:
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is required")
    with SessionLocal() as db:
        inserted = fetch_and_save(db)
        logger.info("celery ingest complete: inserted=%s", inserted)
        return inserted


@celery_app.task(name="nlp.process_unprocessed")
def task_process_unprocessed(limit: int = 100) -> int:
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is required")
    ids = _find_unprocessed_headline_ids(limit=limit)
    processed = 0
    with SessionLocal() as db:
        for hid in ids:
            try:
                process_headline(db, hid)
                processed += 1
            except Exception:
                logger.exception("celery failed processing headline_id=%s", hid)
    logger.info("celery processed %d headlines", processed)
    return processed


# Optional beat schedule example (if using celery beat in future):
# from celery.schedules import crontab
# celery_app.conf.beat_schedule = {
#     "ingest-every-5-min": {
#         "task": "ingest.fetch_and_save",
#         "schedule": 300.0,  # seconds
#     },
#     "process-unprocessed-every-5-min": {
#         "task": "nlp.process_unprocessed",
#         "schedule": 300.0,
#     },
# }


