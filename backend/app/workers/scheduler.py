import os
import time
import logging
from typing import List

from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.headline import Headline
from app.models.mention import Mention
from app.models.risk_score import RiskScore
from app.ingest.news_fetcher import fetch_and_save
from app.nlp.processor import process_headline


load_dotenv()


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("scheduler")


def _find_unprocessed_headline_ids(limit: int = 100) -> List[int]:
    """Return headline ids that have no mentions and no risk_scores yet."""
    with SessionLocal() as db:
        q = (
            select(Headline.id)
            .outerjoin(Mention, Mention.headline_id == Headline.id)
            .outerjoin(RiskScore, RiskScore.headline_id == Headline.id)
            .where(Mention.id.is_(None), RiskScore.id.is_(None))  # type: ignore
            .order_by(Headline.id.desc())
            .limit(limit)
        )
        rows = db.execute(q).scalars().all()
        return list(rows)


def job_ingest_and_process() -> None:
    """Periodic job: fetch + save headlines, then process any unprocessed ones."""
    logger.info("job start: ingest and process")

    # Ingest
    try:
        with SessionLocal() as db:
            inserted = fetch_and_save(db)
            logger.info("ingest complete: inserted=%s", inserted)
    except Exception as exc:
        logger.exception("ingest error: %s", exc)

    # Process unprocessed
    try:
        ids = _find_unprocessed_headline_ids(limit=100)
        if not ids:
            logger.info("no unprocessed headlines found")
            return
        logger.info("processing %d headlines", len(ids))
        with SessionLocal() as db:
            for hid in ids:
                try:
                    process_headline(db, hid)
                except Exception:
                    logger.exception("failed processing headline_id=%s", hid)
    except Exception as exc:
        logger.exception("processing phase error: %s", exc)


def main() -> None:
    # Basic sanity for required env
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is required")

    scheduler = BackgroundScheduler()
    scheduler.add_job(job_ingest_and_process, "interval", minutes=5, id="ingest_process_5m", max_instances=1)
    scheduler.start()

    logger.info("APScheduler started. Running every 5 minutes. Press Ctrl+C to exit.")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("shutting down scheduler...")
        scheduler.shutdown()


if __name__ == "__main__":
    main()


