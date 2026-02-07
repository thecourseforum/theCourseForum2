"""Shared helper utilities for view logic."""

from django.utils.http import url_has_allowed_host_and_scheme


def safe_next_url(request, default_url: str) -> str:
    """Return validated next URL when present, otherwise default."""
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return default_url
