"""Custom tags and filters to be used in templates."""

from urllib.parse import urlencode

from django import template

register = template.Library()

COURSE_FILTER_KEYS = {
    "discipline",
    "subdepartment",
    "weekdays",
    "from_time",
    "to_time",
    "open_sections",
    "min_gpa",
}


@register.filter
def get_item(dictionary, key):
    """Return a dictionary item for template access."""
    return dictionary.get(key)


@register.filter
def remove_email(value):
    """Remove instructor email suffix from display strings."""
    return str(value).split("(", maxsplit=1)[0]


def _split_csv_keys(raw_keys):
    """Split comma-separated key strings into a clean key list."""
    if not raw_keys:
        return []
    return [key.strip() for key in str(raw_keys).split(",") if key.strip()]


def _querydict_to_lists(query_dict):
    """Convert QueryDict to a mutable dict[str, list[str]]."""
    return {
        key: [str(value) for value in values]
        for key, values in query_dict.lists()
    }


@register.simple_tag
def querystring(request, include="", remove="", **overrides):
    """Build an encoded querystring with include/remove/override support."""
    params = _querydict_to_lists(request.GET)

    include_keys = set(_split_csv_keys(include))
    if include_keys:
        params = {
            key: values
            for key, values in params.items()
            if key in include_keys
        }

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
    url_name = getattr(request.resolver_match, "url_name", "")
    allowed = {"q"}
    if url_name == "search" and target_mode == "courses":
        allowed = allowed.union(COURSE_FILTER_KEYS)

    params = {
        key: values
        for key, values in _querydict_to_lists(request.GET).items()
        if key in allowed
    }
    params["mode"] = [str(target_mode)]
    params.pop("page", None)

    query = urlencode(params, doseq=True)
    if not query:
        return request.path
    return f"{request.path}?{query}"


@register.simple_tag
def getlist_contains(request, key, value):
    """Return True when value exists in request.GET list for key."""
    values = request.GET.getlist(key)
    return str(value) in values
