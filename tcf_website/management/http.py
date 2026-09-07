"""Shared ``requests`` setup for management commands that call external HTTPS APIs."""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def requests_session_with_pool_and_retries(
    *,
    workers: int,
    status_forcelist,
    backoff_factor=1,
    retry_total=4,
    allowed_methods=None,
):
    """Session with connection pool ``workers`` wide and urllib3 retries on status codes."""
    if allowed_methods is not None:
        retry = Retry(
            total=retry_total,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            allowed_methods=allowed_methods,
        )
    else:
        retry = Retry(
            total=retry_total,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
    session = requests.Session()
    adapter = HTTPAdapter(
        pool_connections=workers,
        pool_maxsize=workers,
        max_retries=retry,
    )
    session.mount("https://", adapter)
    return session
