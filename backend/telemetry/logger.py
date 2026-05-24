from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from backend.telemetry.tracing import current_trace_context


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace": current_trace_context().to_dict(),
        }
        for key in ("event", "worker_id", "job_id", "queue_name", "municipality_id", "status", "error"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        for key, value in record.__dict__.items():
            if key.startswith("civiceye_"):
                payload[key.removeprefix("civiceye_")] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, separators=(",", ":"))


def configure_logging() -> None:
    root = logging.getLogger()
    if any(isinstance(handler.formatter, JsonLogFormatter) for handler in root.handlers):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def log_event(logger_name: str, event: str, message: str, **extra: Any) -> None:
    logging.getLogger(logger_name).info(message, extra={"event": event, **extra})
