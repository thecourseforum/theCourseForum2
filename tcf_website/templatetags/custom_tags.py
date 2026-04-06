"""Custom tags and filters to be used in templates."""

from urllib.parse import urlencode

from django import template
from django.urls import reverse

from ..stat_display import stat_display_value
from ..utils import update_query_params, with_mode

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Return a dictionary item for template access."""
    return dictionary.get(key)


@register.filter
def remove_email(value):
    """Remove instructor email suffix from display strings."""
    return str(value).split("(", maxsplit=1)[0]


@register.filter
def stat_display(value, kind):
    """Normalize a stat for display: missing or sentinel values become None."""
    return stat_display_value(kind, value)


def _split_csv_keys(raw_keys):
    """Split comma-separated key strings into a clean key list."""
    if not raw_keys:
        return []
    return [key.strip() for key in str(raw_keys).split(",") if key.strip()]


def _querydict_to_lists(query_dict):
    """Convert QueryDict to a mutable dict[str, list[str]]."""
    return {key: [str(value) for value in values] for key, values in query_dict.lists()}


@register.simple_tag
def querystring(request, include="", remove="", **overrides):
    """Build an encoded querystring with include/remove/override support."""
    params = _querydict_to_lists(request.GET)

    include_keys = set(_split_csv_keys(include))
    if include_keys:
        params = {key: values for key, values in params.items() if key in include_keys}

    remove_keys = set(_split_csv_keys(remove))
    for key in remove_keys:
        params.pop(key, None)

    for key, value in overrides.items():
        if value in (None, ""):
            params.pop(key, None)
        else:
            params[key] = [str(value)]

    return urlencode(params, doseq=True)


@register.simple_tag
def mode_toggle_url(request, target_mode):
    """Build a mode-toggle URL while preserving an allowlist of query parameters."""
    url = update_query_params(request.path, q=request.GET.get("q"))
    return with_mode(url, target_mode)


@register.simple_tag
def mode_url(request, view_name, *args, **kwargs):
    """Reverse a URL and preserve or override the current mode query parameter."""
    target_mode = kwargs.pop("mode", request.GET.get("mode"))
    query_kwargs = {}

    for key in list(kwargs):
        if key.startswith("query_"):
            query_kwargs[key.removeprefix("query_")] = kwargs.pop(key)

    url = reverse(view_name, args=args, kwargs=kwargs)
    url = update_query_params(url, **query_kwargs)
    return with_mode(url, target_mode)
