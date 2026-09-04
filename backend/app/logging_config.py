"""
Structured logging setup.

Every log line is a single JSON object so that request_id / session_id /
provider / latency fields (section 24) can be grepped or shipped to a log
aggregator without regex parsing. Secrets are never logged — callers must
not pass api keys or raw user PII into `extra`.
"""
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from app.config import settings

_REDACT_KEYS = {"api_key", "anthropic_api_key", "authorization", "password"}

# Attribute names every LogRecord carries by default (stdlib docs). Anything
# NOT in this set was passed via `extra=` on the log call and is genuinely
# request-specific context worth surfacing (request_id, session_id, ...).
_STANDARD_RECORD_KEYS = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "taskName", "message", "asctime",
}


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Anything passed via `extra=` on the log call ends up as attributes
        # on the record; surface it, redacting anything sensitive.
        for key, value in record.__dict__.items():
            if key in _STANDARD_RECORD_KEYS:
                continue
            if key.lower() in _REDACT_KEYS:
                continue
            payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        import json

        return json.dumps(payload, default=str)


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)

    # Quiet down noisy third-party loggers unless we're debugging.
    for noisy in ("uvicorn.access", "httpx", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(
            "WARNING" if settings.log_level.upper() != "DEBUG" else "DEBUG"
        )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
