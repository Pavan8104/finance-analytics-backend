"""
Structured JSON logger for the Finance Analytics API.

Outputs machine-parseable JSON logs suitable for ingestion by
Datadog, CloudWatch, Loki, or any log aggregation platform.
"""
import logging
import logging.handlers
import sys
from pathlib import Path

from app.core.config import settings


LOG_DIR = Path("logs")


def _build_logger() -> logging.Logger:
    log = logging.getLogger("finance_api")

    # Avoid adding duplicate handlers if called multiple times
    if log.handlers:
        return log

    log.setLevel(logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO)
    log.propagate = False

    # --- Formatter ---
    try:
        # python-json-logger v3/v4 API
        from pythonjsonlogger.jsonlogger import JsonFormatter  # type: ignore
        formatter = JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    except Exception:
        # Fallback to standard formatter if package API has changed
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )

    # --- Console handler (always active) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)

    # --- Rotating file handler (skipped in test environments) ---
    if settings.ENVIRONMENT not in ("test", "testing"):
        try:
            LOG_DIR.mkdir(exist_ok=True)
            file_handler = logging.handlers.RotatingFileHandler(
                LOG_DIR / "app.log",
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            log.addHandler(file_handler)
        except OSError:
            pass  # Silently skip file logging if directory is not writable

    return log


logger = _build_logger()
