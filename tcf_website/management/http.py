"""Shared ``requests`` setup for management commands that call external HTTPS APIs."""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def requests_session_with_pool_and_retries(
    *,
    workers,
    status_forcelist,
    backoff_factor=1,
    retry_total=4,
    allowed_methods=None,
):
    """Session with connection pool ``workers`` wide and urllib3 retries on status codes."""
    retry_kw = {
        "total": retry_total,
        "backoff_factor": backoff_factor,
        "status_forcelist": status_forcelist,
    }
    if allowed_methods is not None:
        retry_kw["allowed_methods"] = allowed_methods
    session = requests.Session()
    adapter = HTTPAdapter(
        pool_connections=workers,
        pool_maxsize=workers,
        max_retries=Retry(**retry_kw),
    )
    session.mount("https://", adapter)
    return session
