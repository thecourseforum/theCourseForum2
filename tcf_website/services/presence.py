"""Service for interacting with the Presence API."""

import logging

import backoff
import requests

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

BASE = f"https://api.presence.io/{settings.PRESENCE_SUBDOMAIN}/v1"
CACHE_TTL = getattr(settings, "PRESENCE_CACHE_SECONDS", 300)
TIMEOUT = getattr(settings, "PRESENCE_TIMEOUT_SECONDS", 8)

# Use a session with browser-like headers so the API allows the request (avoids 403 in some environments)
_SESSION = requests.Session()
_SESSION.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (compatible; theCourseForum/1.0; +https://thecourseforum.com)",
        "Accept": "application/json",
    }
)


def _cache_key(key: str) -> str:
    return f"presence::{settings.PRESENCE_SUBDOMAIN}::{key}"


@backoff.on_exception(backoff.expo, (requests.RequestException,), max_tries=3)
def _get(url: str, params: dict | None = None) -> dict:
    resp = _SESSION.get(url, params=params or {}, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_events():
    """
    Returns a list of upcoming events from Presence. Cached briefly to avoid rate limits.
    On API errors (e.g. 403 Forbidden in local dev), returns an empty list so the page still loads.
    """
    key = _cache_key("events_all")
    data = cache.get(key)
    if data is None:
        try:
            data = _get(f"{BASE}/events")
            cache.set(key, data, CACHE_TTL)
        except requests.HTTPError as e:
            logger.warning(
                "Presence API error (events): %s %s - %s",
                e.response.status_code if e.response is not None else "?",
                e.response.reason if e.response is not None else "",
                str(e),
            )
            return []
        except requests.RequestException as e:
            logger.warning("Presence API request failed (events): %s", e)
            return []
    return data


def get_event_details(event_uri: str):
    key = _cache_key(f"event::{event_uri}")
    data = cache.get(key)
    if data is None:
        try:
            data = _get(f"{BASE}/events/{event_uri}")
            cache.set(key, data, CACHE_TTL)
        except requests.HTTPError as e:
            logger.warning(
                "Presence API error (event %s): %s %s",
                event_uri,
                e.response.status_code if e.response is not None else "?",
                e.response.reason if e.response is not None else "",
            )
            return None
        except requests.RequestException as e:
            logger.warning("Presence API request failed (event %s): %s", event_uri, e)
            return None
    return data


