"""Middleware and logging helpers that tag every log line with a request ID."""

import json
import logging
import re
import time
import uuid
from contextvars import ContextVar

from django.contrib.auth import SESSION_KEY

logger = logging.getLogger(__name__)

request_id_var = ContextVar("request_id", default="-")

VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9_=-]{1,128}$")
REQUEST_FIELDS = ("method", "path", "status", "duration_ms", "user_id")


class RequestLogMiddleware:
    """Assigns a request ID and logs one line per request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        header = request.headers.get("X-Amz-Cf-Id", "")
        request.request_id = (
            header if VALID_REQUEST_ID.match(header) else uuid.uuid4().hex
        )
        token = request_id_var.set(request.request_id)
        start = time.monotonic()
        try:
            response = self.get_response(request)
            session = getattr(request, "session", None)
            logger.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": round((time.monotonic() - start) * 1000),
                    "user_id": session.get(SESSION_KEY)
                    if session is not None
                    else None,
                },
            )
            return response
        finally:
            request_id_var.reset(token)


class RequestIdFilter(logging.Filter):
    """Sets request_id on every log record."""

    def filter(self, record):
        request = getattr(record, "request", None)
        record.request_id = getattr(request, "request_id", None) or request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """Formats a log record as a single JSON line."""

    def format(self, record):
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        for field in REQUEST_FIELDS:
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        if record.exc_info:
            payload["traceback"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class TextFormatter(logging.Formatter):
    """Formats a log record as readable plain text."""

    def formatMessage(self, record):
        request_id = getattr(record, "request_id", "-")
        prefix = record.levelname
        if request_id != "-":
            prefix = f"{prefix} [{request_id[:8]}]"
        if not hasattr(record, "status"):
            return f"{prefix} {record.name}: {record.message}"
        line = (
            f"{prefix} {record.method} {record.path} "
            f"{record.status} {record.duration_ms}ms"
        )
        return f"{line} user={record.user_id}" if record.user_id else line
