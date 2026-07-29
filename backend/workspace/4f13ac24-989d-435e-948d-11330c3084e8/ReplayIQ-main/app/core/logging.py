"""
Structured Logging (Phase 9).

Configures Python's built-in logging module with JSON-formatted output.
No external dependencies — uses stdlib logging + json.

Usage:
    from app.core.logging import logger
    logger.info("Request processed", extra={"path": "/api/v1/projects"})

Log level is controlled by the LOG_LEVEL environment variable (default: INFO).
"""

import logging
import json
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as single-line JSON objects.
    This makes logs easy to parse by log aggregation tools (ELK, CloudWatch, etc.).
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include any extra fields passed via the `extra` kwarg
        # (e.g. logger.info("msg", extra={"path": "/api/v1/..."}) )
        for key in ("path", "method", "status_code", "error_code", "detail"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        # Parse uvicorn access logs if name matches and record args are present
        if record.name == "uvicorn.access" and record.args and len(record.args) >= 5:
            # record.args layout: (client_addr, method, path, http_version, status_code)
            log_entry["client_ip"] = record.args[0]
            log_entry["method"] = record.args[1]
            log_entry["path"] = record.args[2]
            log_entry["status_code"] = record.args[4]

        # Include exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Creates and configures the application-wide logger.
    Should be called once during app startup.
    """
    logger = logging.getLogger("replayiq")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Avoid adding duplicate handlers if called more than once
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    # Prevent logs from propagating to the root logger (avoids duplicate output)
    logger.propagate = False

    # Standardize and format Uvicorn logs for production environments
    for uvicorn_logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        u_logger = logging.getLogger(uvicorn_logger_name)
        u_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        # Clear existing handlers to prevent duplicate plain text logs
        for h in list(u_logger.handlers):
            u_logger.removeHandler(h)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        u_logger.addHandler(handler)
        u_logger.propagate = False

    return logger


# Module-level logger instance for convenience imports
logger = setup_logging()
