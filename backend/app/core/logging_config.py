"""Centralized logging configuration for Declairo."""
from __future__ import annotations

import copy
import json
import logging
import logging.config
from datetime import datetime, timezone
from typing import Any


class JSONFormatter(logging.Formatter):
    """Emit logs as single-line JSON for log aggregation systems."""

    def format(self, record: logging.LogRecord) -> str:
        log = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "request_id"):
            log["request_id"] = record.request_id
        return json.dumps(log, ensure_ascii=False)


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": "app.core.logging_config.JSONFormatter"},
        "plain": {"format": "%(asctime)s %(levelname)-8s %(name)s — %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "json",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "uvicorn": {"level": "INFO", "propagate": True},
        "sqlalchemy.engine": {"level": "WARNING", "propagate": True},
    },
}


def setup_logging(json_format: bool = True) -> None:
    config: dict[str, Any] = copy.deepcopy(LOGGING_CONFIG)
    if not json_format:
        config["handlers"]["console"]["formatter"] = "plain"
    logging.config.dictConfig(config)
