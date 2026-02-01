"""
Analytics tracking metric for course and instructor page views
Uses DynamoDB atomic counters with non-blocking concept to ensure analytics never block user requests
Handles high traffic with bounded thread pool and overflow protection (Limit on backlog)
"""

import atexit
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from decouple import config

logger = logging.getLogger(__name__)

# Configuration

# Maximum number of pending analytics tasks before dropping events
_MAX_BACKLOG = 100
# Number of worker threads for processing,
_MAX_WORKERS = 5
_TTL_DAYS = config("ANALYTICS_TTL_DAYS", default=2, cast=int)

# Thread Pool Setup

# Track pending tasks to prevent overflow
_pending = 0
_pending_lock = threading.Lock()
# Thread pool for background analytics processing
_EXECUTOR = ThreadPoolExecutor(
    max_workers=_MAX_WORKERS, thread_name_prefix="analytics-worker-"
)

# DynamoDB Setup

# Timeout configuration to prevent thread exhaustion
_BOTO_CONFIG = Config(
    connect_timeout=2,  # Fail if no connection within 2 seconds
    read_timeout=3,  # Fail if AWS doesn't respond within 3 seconds
    retries={"max_attempts": 1},  # Don't retry if fail
)
# Initialize DynamoDB session
try:
    _SESSION = boto3.Session(
        aws_access_key_id=config("AWS_ANALYTICS_ACCESS_KEY_ID"),
        aws_secret_access_key=config("AWS_ANALYTICS_SECRET_ACCESS_KEY"),
        region_name=config("AWS_REGION", default="us-east-1"),
    )
    _DYNAMODB = _SESSION.resource("dynamodb", config=_BOTO_CONFIG)
    logger.info("Analytics DynamoDB session initialized")
except Exception as e:
    _SESSION = None
    _DYNAMODB = None
    logger.error(f"Failed to initialize analytics: {e}")

# Core Analytics Functions


def _send_to_dynamo(entity_type: str, entity_id: int) -> None:
    """
    Atomically increment view count in DynamoDB

    Uses composite key: pk (entity_type & entity_id), sk (YYYY-MM-DD)
    Sets TTL based on TTL_DAYS config for automatic cleanup

    Arguments: Type (course or instructor) and id (Numeric ID of the entity)
    """
    if _DYNAMODB is None:
        return  # Skip if DynamoDB session failed to initailize

    try:
        table = _DYNAMODB.Table(config("DYNAMODB_TABLE_NAME"))

        # Get current UTC time (for consistency)
        now = datetime.now(timezone.utc)
        today = now.date().isoformat()  # YYYY-MM-DD
        composite_key = f"{entity_type}:{entity_id}"
        expiration_time = int(now.timestamp()) + (_TTL_DAYS * 24 * 60 * 60)

        # Atomic increment in DynamoDB
        table.update_item(
            Key={"pk": composite_key, "sk": today},
            UpdateExpression="ADD view_count :inc SET expires_at = :ttl",
            ExpressionAttributeValues={":inc": 1, ":ttl": expiration_time},
        )

        logger.debug(f"Recorded view for {composite_key} on {today}")

    except ClientError as e:
        # AWS-specific Errors (Access Denied, Table Not Found, etc)
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        logger.error(
            f"DynamoDB ClientError for {entity_type}:{entity_id}: {error_code}"
        )
    except Exception as e:
        # Network errors, timeouts, etc
        logger.error(f"Analytics failed for {entity_type}:{entity_id}: {e}")


def _fire_and_forget(entity_type: str, entity_id: int) -> None:
    """
    Submit analytics task to bounded thread pool without blocking

    Implements overflow protections by dropping events when backlog is full (site stability >>> analytic accuracy)

    Args: Type (course or instructor) & ID (Numeric ID of the entity)
    """
    global _pending

    # Check if backlog is full (with lock for thread safety)
    with _pending_lock:
        if _pending >= _MAX_BACKLOG:
            logger.warning(
                f"Analytics backlog full ({_pending}/{_MAX_BACKLOG}). "
                f"Dropping event for {entity_type}:{entity_id}"
            )
            return  # Drop event to preserve site stability
        _pending += 1

    # Wrapper ensures pending count decrements even on error
    def task_wrapper():
        global _pending
        try:
            _send_to_dynamo(entity_type, entity_id)
        finally:
            with _pending_lock:
                _pending -= 1

    # Submit task to thread pool (Send up)
    try:
        _EXECUTOR.submit(task_wrapper)
    except Exception as e:
        # Executor submission failed (shutdown, etc)
        with _pending_lock:
            _pending -= 1
        logger.error(f"Failed to submit analytics task: {e}")


# Public API
def record_course_view(course_id: int) -> None:
    """
    Record a page view for a course (non-blocking)
    Args: ID (Numeric ID of the COURSE)
    """
    _fire_and_forget("course", course_id)


def record_instructor_view(instructor_id: int) -> None:
    """
    Record a page view for an instructor (non-blocking)
    Args: ID (Numeric ID of the INSTRUCTOR)
    """
    _fire_and_forget("instructor", instructor_id)


def get_analytics_health() -> dict:
    """
    Get current health status of the analytics system

    Returns: status (healthy/session_failed), pending_tasks (# waiting to be processed), max_backlog (max pending tasks),
    utilization_percent (backlog use 0-100), workers (number of workers threads), ttl_days (days before data expires)

    Can Check with:
       python manage.py shell
       from tcf_website.analytics_utils import get_analytics_health
       print(get_analytics_health())
    will see:
    {'status': 'healthy', 'pending_tasks': 0, 'max_backlog': 100, 'utilization_percent': 0.0, 'workers': 5}
    """
    with _pending_lock:
        pending = _pending

    return {
        "status": "healthy" if _SESSION else "session_failed",
        "pending_tasks": pending,
        "max_backlog": _MAX_BACKLOG,
        "utilization_percent": round((pending / _MAX_BACKLOG) * 100, 1),
        "workers": _MAX_WORKERS,
        "ttl_days": _TTL_DAYS,
    }


# Shutdown Handler
def _shutdown_executor():
    """
    Gracefully shutdown the thread pool on app exit
    Waits for pending tasks
    """
    with _pending_lock:
        pending_count = _pending

    if pending_count > 0:
        logger.info(f"Shutting down analytics ({pending_count} pending)")

    _EXECUTOR.shutdown(wait=True, cancel_futures=False)


# Register shutdown handler
atexit.register(_shutdown_executor)
