import requests
import backoff
from django.conf import settings
from django.core.cache import cache

BASE = f"https://api.presence.io/{settings.PRESENCE_SUBDOMAIN}/v1"
CACHE_TTL = getattr(settings, "PRESENCE_CACHE_SECONDS", 300)
TIMEOUT = getattr(settings, "PRESENCE_TIMEOUT_SECONDS", 8)


def _cache_key(key: str) -> str:
    return f"presence::{settings.PRESENCE_SUBDOMAIN}::{key}"


@backoff.on_exception(backoff.expo, (requests.RequestException,), max_tries=3)
def _get(url: str, params=None):
    resp = requests.get(url, params=params or {}, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_events():
    """
    Returns a list of upcoming events from Presence. Cached briefly to avoid rate limits.
    """
    key = _cache_key("events_all")
    data = cache.get(key)
    if data is None:
        data = _get(f"{BASE}/events")
        cache.set(key, data, CACHE_TTL)
    return data


def get_event_details(event_uri: str):
    key = _cache_key(f"event::{event_uri}")
    data = cache.get(key)
    if data is None:
        data = _get(f"{BASE}/events/{event_uri}")
        cache.set(key, data, CACHE_TTL)
    return data


