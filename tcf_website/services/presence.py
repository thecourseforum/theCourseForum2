"""Service for interacting with the Presence API."""

import backoff
import requests

from django.conf import settings
from django.core.cache import cache

BASE = f"https://api.presence.io/{settings.PRESENCE_SUBDOMAIN}/v1"
CACHE_TTL = getattr(settings, "PRESENCE_CACHE_SECONDS", 300)
TIMEOUT = getattr(settings, "PRESENCE_TIMEOUT_SECONDS", 8)


def _cache_key(key: str) -> str:
    """
    Builds a namespaced cache key for Presence-related data.
    
    Parameters:
        key (str): The key suffix identifying the cached item (e.g., "events_all" or "event::<uri>").
    
    Returns:
        str: A cache key of the form "presence::{subdomain}::{key}", where {subdomain} is the configured Presence subdomain.
    """
    return f"presence::{settings.PRESENCE_SUBDOMAIN}::{key}"


@backoff.on_exception(backoff.expo, (requests.RequestException,), max_tries=3)
def _get(url: str, params: dict | None = None) -> dict:
    """
    Retrieve and parse JSON from the specified URL.
    
    Parameters:
        params (dict | None): Optional query parameters to include in the request.
    
    Returns:
        dict: Parsed JSON response as a dictionary.
    
    Raises:
        requests.RequestException: If the HTTP request fails or the response has a non-2xx status.
    """
    resp = requests.get(url, params=params or {}, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_events():
    """
    Retrieve upcoming events from Presence, using a short-lived cache to reduce API calls.
    
    Returns:
        dict: Parsed JSON response from the Presence `/events` endpoint containing the list of upcoming events and related metadata.
    """
    key = _cache_key("events_all")
    data = cache.get(key)
    if data is None:
        data = _get(f"{BASE}/events")
        cache.set(key, data, CACHE_TTL)
    return data


def get_event_details(event_uri: str):
    """
    Retrieve and cache details for a specific Presence event.
    
    Parameters:
        event_uri (str): The event's URI or identifier relative to the Presence API (used to build the request path).
    
    Returns:
        dict: Parsed JSON containing the event details. The result is cached under a namespaced key for CACHE_TTL seconds.
    """
    key = _cache_key(f"event::{event_uri}")
    data = cache.get(key)
    if data is None:
        data = _get(f"{BASE}/events/{event_uri}")
        cache.set(key, data, CACHE_TTL)
    return data

