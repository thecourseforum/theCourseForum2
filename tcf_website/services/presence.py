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
    Construct a namespaced cache key for Presence data.
    
    Parameters:
        key (str): The key to be namespaced for caching.
    
    Returns:
        str: Cache key prefixed with the Presence subdomain and module namespace.
    """
    return f"presence::{settings.PRESENCE_SUBDOMAIN}::{key}"


@backoff.on_exception(backoff.expo, (requests.RequestException,), max_tries=3)
def _get(url: str, params: dict | None = None) -> dict:
    """
    Fetches JSON from the specified URL via HTTP GET.
    
    Parameters:
        url: The request URL.
        params: Optional query parameters to include in the request.
    
    Returns:
        dict: Parsed JSON response.
    
    Raises:
        requests.HTTPError: If the HTTP response status indicates an error.
    """
    resp = requests.get(url, params=params or {}, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_events():
    """
    Retrieve the list of upcoming Presence events.
    
    The parsed JSON response is cached for CACHE_TTL seconds to reduce API calls and avoid rate limits; on cache miss the function requests the data from the Presence API.
    
    Returns:
        dict: Parsed JSON response from the Presence API containing upcoming events.
    """
    key = _cache_key("events_all")
    data = cache.get(key)
    if data is None:
        data = _get(f"{BASE}/events")
        cache.set(key, data, CACHE_TTL)
    return data


def get_event_details(event_uri: str):
    """
    Retrieve details for a specific Presence event identified by its URI.
    
    The result is cached under a presence‑namespaced key for the configured CACHE_TTL; a cache miss triggers a request to the Presence API.
    
    Parameters:
        event_uri (str): The event's URI or identifier appended to the API path (e.g. "my-event-slug").
    
    Returns:
        dict: Event details as returned by the Presence API.
    """
    key = _cache_key(f"event::{event_uri}")
    data = cache.get(key)
    if data is None:
        data = _get(f"{BASE}/events/{event_uri}")
        cache.set(key, data, CACHE_TTL)
    return data

