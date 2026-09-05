import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from app.config import settings


REDACT_KEYS = {
    "api_key",
    "anthropic_api_key",
    "authorization",
    "password",
}

STANDARD_RECORD_KEYS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "taskName",
    "message",
    "asctime",
}


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key in STANDARD_RECORD_KEYS:
                continue

            if key.lower() in REDACT_KEYS:
                continue

            data[key] = value

        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(data, default=str)


def configure_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger.addHandler(handler)

    log_level = settings.log_level.upper()

    for logger_name in (
        "uvicorn.access",
        "httpx",
        "sqlalchemy.engine",
    ):
        logging.getLogger(logger_name).setLevel(
            "DEBUG" if log_level == "DEBUG" else "WARNING"
        )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)