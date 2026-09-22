import logging
import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID


class SafeJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles common non-serializable types."""

    def default(self, obj):
        if isinstance(obj, (datetime,)):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        # Fallback to string representation
        return str(obj)


class JsonFormatter(logging.Formatter):
    # Standard logging record attributes to exclude from extra fields
    STANDARD_ATTRS = {
        'name', 'msg', 'args', 'created', 'filename', 'funcName', 'levelname',
        'levelno', 'lineno', 'module', 'msecs', 'message', 'pathname', 'process',
        'processName', 'relativeCreated', 'thread', 'threadName', 'exc_info',
        'exc_text', 'stack_info', 'taskName'
    }

    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Exception handling (split into structured fields)
        if record.exc_info:
            log_record["exception_type"] = record.exc_info[0].__name__
            log_record["exception_message"] = str(record.exc_info[1])
            log_record["exception_traceback"] = self.formatException(record.exc_info)

        # Capture any extra fields passed via logger.info(..., extra={})
        for key, value in record.__dict__.items():
            if key not in self.STANDARD_ATTRS and not key.startswith('_'):
                log_record[key] = value

        # Safe JSON serialization with fallback
        try:
            return json.dumps(log_record, cls=SafeJSONEncoder)
        except (TypeError, ValueError) as e:
            # Fallback: convert all values to strings
            safe_record = {k: str(v) for k, v in log_record.items()}
            safe_record["json_encoding_error"] = str(e)
            return json.dumps(safe_record)
