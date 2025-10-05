import logging
import os
from typing import Optional

try:
    from pythonjsonlogger import jsonlogger  # type: ignore
except Exception:  # pragma: no cover
    jsonlogger = None  # type: ignore


def setup_logging(level: Optional[str] = None) -> None:
    """Configure application-wide structured logging.

    - Uses JSON logs when python-json-logger is available; otherwise falls back to plain text.
    - Default level is INFO (override via LOG_LEVEL env).
    """
    log_level_str = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    root = logging.getLogger()
    root.setLevel(log_level)

    # Clear existing handlers to avoid duplicates in reloads/tests
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler()

    if jsonlogger is not None:
        fmt = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"levelname": "level", "asctime": "timestamp"},
        )
        handler.setFormatter(fmt)
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
        handler.setFormatter(formatter)

    root.addHandler(handler)


