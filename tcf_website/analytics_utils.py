import atexit
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import boto3
import environ
from botocore.config import Config

logger = logging.getLogger(__name__)
env = environ.Env()

# Configuration
_MAX_BACKLOG = 100
_MAX_WORKERS = 5
_TTL_DAYS = max(1, env.int("ANALYTICS_TTL_DAYS", default=7))  # Minimum 1 day TTL
_BOTO_CONFIG = Config(connect_timeout=2, read_timeout=3, retries={"max_attempts": 1})

# State Management
_pending = 0
_pending_lock = threading.Lock()
_EXECUTOR = ThreadPoolExecutor(
    max_workers=_MAX_WORKERS, thread_name_prefix="analytics-worker-"
)

# Global Session (Thread-safe)
_SESSION = None
_ANALYTICS_ENABLED = False

try:
    access_key = env("AWS_ANALYTICS_ACCESS_KEY_ID", default=None)
    secret_key = env("AWS_ANALYTICS_SECRET_ACCESS_KEY", default=None)
    session_kwargs = {"region_name": env("AWS_REGION", default="us-east-1")}
    if access_key and secret_key:
        session_kwargs.update(
            {
                "aws_access_key_id": access_key,
                "aws_secret_access_key": secret_key,
            }
        )
    _SESSION = boto3.Session(**session_kwargs)
    _ANALYTICS_ENABLED = True
except Exception as e:
    logger.error(f"Analytics initialization failed: {e}")


def get_table():
    """Returns a DynamoDB Table resource, or None if analytics is disabled."""
    # OLD: if not _SESSION:
    if not _ANALYTICS_ENABLED:
        return None
        
    return _SESSION.resource("dynamodb", config=_BOTO_CONFIG).Table(
        env("DYNAMODB_TABLE_NAME", default="trending_analytics")
    )


def _send_to_dynamo(entity_type: str, entity_id: int) -> None:
    """Worker function: Creates per-thread resource from global session."""
    if not _SESSION:
        return

    table = get_table()
    try:
        now = datetime.now(UTC)
        pk = f"{entity_type}:{entity_id}"
        sk = now.date().isoformat()
        ttl = int(now.timestamp()) + (_TTL_DAYS * 24 * 60 * 60)

        table.update_item(
            Key={"pk": pk, "sk": sk},
            UpdateExpression="ADD view_count :inc SET expires_at = if_not_exists(expires_at, :ttl), entity_type = :et",
            ExpressionAttributeValues={":inc": 1, ":ttl": ttl, ":et": entity_type},
        )
    except Exception as e:
        logger.warning(f"DynamoDB update failed for {entity_type}:{entity_id}: {e}")


def _fire_and_forget(entity_type: str, entity_id: int) -> None:
    if not _ANALYTICS_ENABLED:
        return
    global _pending
    with _pending_lock:
        if _pending >= _MAX_BACKLOG:
            return
        _pending += 1

    def task_wrapper():
        global _pending
        try:
            _send_to_dynamo(entity_type, entity_id)
        finally:
            with _pending_lock:
                _pending -= 1

    try:
        _EXECUTOR.submit(task_wrapper)
    except Exception as e:
        with _pending_lock:
            _pending -= 1
        logger.error(
            f"Failed to submit analytics task for {entity_type}:{entity_id}: {e}"
        )


def record_course_view(course_id: int) -> None:
    _fire_and_forget("course", course_id)


def record_instructor_view(instructor_id: int) -> None:
    _fire_and_forget("instructor", instructor_id)


@atexit.register
def _shutdown_executor():
    _EXECUTOR.shutdown(wait=True)
