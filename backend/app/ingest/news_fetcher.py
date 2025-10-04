import os
import hashlib
import datetime as dt
from typing import Any, Dict, Iterable, List, Optional

import aiohttp
import feedparser
from email.utils import parsedate_to_datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.headline import Headline


def _parse_datetime(value: Optional[str]) -> Optional[dt.datetime]:
    """Parse various datetime string formats to aware datetime (UTC).

    Handles ISO-8601 with 'Z' suffix and common RSS date formats.
    """
    if not value:
        return None

    # Try ISO-8601 (e.g., 2025-10-02T12:00:00Z)
    try:
        iso_value = value.replace("Z", "+00:00")
        d = dt.datetime.fromisoformat(iso_value)
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(dt.timezone.utc)
    except Exception:
        pass

    # Try RFC 2822 / RSS dates
    try:
        d = parsedate_to_datetime(value)
        if d is not None:
            if d.tzinfo is None:
                d = d.replace(tzinfo=dt.timezone.utc)
            return d.astimezone(dt.timezone.utc)
    except Exception:
        pass

    return None


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_newsapi_article(article: Dict[str, Any]) -> Dict[str, Any]:
    source_obj = article.get("source") or {}
    source_name = source_obj.get("name") if isinstance(source_obj, dict) else None
    title = (article.get("title") or "").strip()
    url = article.get("url")
    published_at = _parse_datetime(article.get("publishedAt"))
    return {
        "text": title,
        "published_at": published_at,
        "source": source_name,
        "url": url,
    }


def _normalize_rss_entry(entry: Any, fallback_source: Optional[str] = None) -> Dict[str, Any]:
    # feedparser entries can be dict-like or objects with attributes
    title = getattr(entry, "title", None) or (entry.get("title") if isinstance(entry, dict) else None) or ""
    link = getattr(entry, "link", None) or (entry.get("link") if isinstance(entry, dict) else None)

    # published fields
    published_str = (
        getattr(entry, "published", None)
        or (entry.get("published") if isinstance(entry, dict) else None)
        or getattr(entry, "updated", None)
        or (entry.get("updated") if isinstance(entry, dict) else None)
    )

    published_at = _parse_datetime(published_str) if published_str else None

    source_name = fallback_source
    if hasattr(entry, "source"):
        try:
            source_name = getattr(entry.source, "title", None) or fallback_source
        except Exception:
            pass

    return {
        "text": str(title).strip(),
        "published_at": published_at,
        "source": source_name,
        "url": link,
    }


async def fetch_from_newsapi(query: str = "stocks OR markets", language: str = "en", page_size: int = 100) -> List[Dict[str, Any]]:
    """Fetch headlines from NewsAPI using the NEWSAPI_KEY environment variable.

    Returns a list of normalized headline dicts: {text, published_at, source, url}.
    """
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        return []

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": language,
        "sortBy": "publishedAt",
        "pageSize": page_size,
    }
    headers = {"X-Api-Key": api_key}

    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params, headers=headers) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
            articles = data.get("articles", []) if isinstance(data, dict) else []
            normalized = []
            for a in articles:
                try:
                    norm = _normalize_newsapi_article(a)
                    if norm.get("text") and norm.get("url"):
                        normalized.append(norm)
                except Exception:
                    continue
            return normalized


def fetch_from_rss(feed_urls: Iterable[str]) -> List[Dict[str, Any]]:
    """Fetch headlines from a list of RSS feeds using feedparser.

    Returns a list of normalized headline dicts: {text, published_at, source, url}.
    """
    items: List[Dict[str, Any]] = []
    for feed_url in feed_urls:
        try:
            parsed = feedparser.parse(feed_url)
        except Exception:
            continue

        feed_title = None
        try:
            feed_title = getattr(parsed.feed, "title", None) if hasattr(parsed, "feed") else None
            if isinstance(parsed, dict):  # extremely defensive; feedparser returns a custom obj
                feed_title = parsed.get("feed", {}).get("title") if parsed.get("feed") else feed_title
        except Exception:
            feed_title = None

        entries = []
        try:
            entries = list(parsed.entries) if hasattr(parsed, "entries") else []
        except Exception:
            entries = []

        for entry in entries:
            try:
                norm = _normalize_rss_entry(entry, fallback_source=feed_title)
                if norm.get("text") and norm.get("url"):
                    items.append(norm)
            except Exception:
                continue

    return items


def save_headlines(db: Session, items: List[Dict[str, Any]]) -> int:
    """Insert new headlines into DB avoiding duplicates by URL or text hash.

    Returns the number of inserted rows.
    """
    if not items:
        return 0

    # Prepare sets for fast duplicate checks (existing in DB)
    incoming_urls = [i.get("url") for i in items if i.get("url")]
    existing_urls: set[str] = set()
    if incoming_urls:
        existing_urls = set(
            r[0] for r in db.execute(select(Headline.url).where(Headline.url.in_(incoming_urls))).all()
        )

    incoming_texts = [str(i.get("text") or "").strip() for i in items if i.get("text")]
    existing_titles: set[str] = set()
    if incoming_texts:
        existing_titles = set(
            r[0] for r in db.execute(select(Headline.title).where(Headline.title.in_(incoming_texts))).all()
        )
    existing_title_hashes = {_sha256(t) for t in existing_titles}

    # Track duplicates within this batch as well
    seen_urls: set[str] = set(u for u in existing_urls if u)
    seen_hashes: set[str] = set(existing_title_hashes)

    inserted = 0
    for i in items:
        title = str(i.get("text") or "").strip()
        if not title:
            continue
        url = i.get("url")
        text_hash = _sha256(title)

        if url and url in seen_urls:
            continue
        if text_hash in seen_hashes:
            continue

        headline = Headline(
            source=i.get("source"),
            url=url,
            title=title,
            published_at=i.get("published_at"),
        )
        db.add(headline)
        inserted += 1
        if url:
            seen_urls.add(url)
        seen_hashes.add(text_hash)

    if inserted:
        db.commit()

    return inserted


# Convenience orchestration used by schedulers/workers
def fetch_and_save(db: Session) -> int:
    """Fetch headlines from configured sources and persist new items.

    Returns number of inserted rows.
    """
    items: List[Dict[str, Any]] = []

    # RSS feeds (lightweight, no auth)
    rss_feeds = [
        "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",  # WSJ Markets
        "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",  # Reuters Biz
        "https://www.investing.com/rss/news_25.rss",  # Investing.com Stocks
    ]
    try:
        items.extend(fetch_from_rss(rss_feeds))
    except Exception:
        pass

    # Optional: NewsAPI if NEWSAPI_KEY is provided
    try:
        import asyncio

        news_items: List[Dict[str, Any]] = []
        try:
            news_items = asyncio.run(fetch_from_newsapi())
        except RuntimeError:
            # Fallback when already inside a running loop (rare for our CLI)
            try:
                loop = asyncio.get_event_loop()
            except Exception:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            try:
                news_items = loop.run_until_complete(fetch_from_newsapi())
            except Exception:
                news_items = []
        except Exception:
            news_items = []
        items.extend(news_items)
    except Exception:
        pass

    if not items:
        return 0
    return save_headlines(db, items)


