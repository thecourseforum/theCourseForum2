"""Calendar views for displaying club events."""

from datetime import datetime, timezone


from django.http import Http404
from django.shortcuts import render
from django.utils.html import strip_tags

from tcf_website.services import presence


def _safe_text(html):
    """
    Return plain text with HTML tags removed and trimmed.
    
    Parameters:
        html (str | None): HTML string to sanitize; falsy values are treated as an empty string.
    
    Returns:
        str: Plain text with HTML tags removed and leading/trailing whitespace trimmed.
    """
    return strip_tags(html or "").strip()


def _sort_key(evt):
    """
    Produce a sortable key for an event that places unknown start times after dated events.
    
    Parameters:
        evt (dict): Event mapping that may include a "start_utc" ISO 8601 UTC datetime string.
    
    Returns:
        str: The event's "start_utc" value if present, otherwise the placeholder "9999-12-31T23:59:59Z".
    """
    return evt.get("start_utc") or "9999-12-31T23:59:59Z"


def _format_datetime(dt_string):
    """
    Format a UTC ISO-8601 datetime string into a human-readable display string.
    
    Parameters:
        dt_string (str | None): UTC datetime in ISO 8601 format (may end with 'Z'), or a falsy value.
    
    Returns:
        str: A formatted datetime like "Friday, January 01, 2021 at 05:00 PM". Returns "TBD" when `dt_string` is falsy. If parsing fails, returns the original `dt_string`.
    """
    if not dt_string:
        return "TBD"
    try:
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return dt.strftime("%A, %B %d, %Y at %I:%M %p")
    except (ValueError, AttributeError):
        return dt_string


def _is_upcoming(dt_string):
    """
    Determine whether an event date is today or in the future.
    
    If `dt_string` is empty or cannot be parsed as an ISO 8601 datetime, the event is treated as upcoming.
    
    Parameters:
        dt_string (str): ISO 8601 UTC datetime string (e.g. "2025-01-01T12:00:00Z") or None.
    
    Returns:
        True if the event occurs today or later, False otherwise.
    """
    if not dt_string:
        return True  # Treat events without dates as upcoming

    try:
        event_dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        return event_dt.date() >= today.date()
    except (ValueError, AttributeError):
        return True


def calendar_overview(request):
    """Display an overview of upcoming and past club events."""
    raw = presence.get_events()
    events = []
    for e in raw or []:
        events.append(
            {
                "name": e.get("eventName"),
                "org": e.get("organizationName"),
                "uri": e.get("uri"),
                "location": e.get("location"),
                "start_utc": e.get("startDateTimeUtc"),
                "end_utc": e.get("endDateTimeUtc"),
                "tags": e.get("tags") or [],
                "desc_text": _safe_text(e.get("description")),
            }
        )

    events.sort(key=_sort_key)

    # Separate upcoming and past events
    upcoming_events = []
    past_events = []

    for ev in events:
        if _is_upcoming(ev["start_utc"]):
            upcoming_events.append(ev)
        else:
            past_events.append(ev)

    # Group upcoming events by date
    upcoming_groups = {}
    for ev in upcoming_events:
        dt = ev["start_utc"] or ""
        date_key = dt[:10] if len(dt) >= 10 else "TBD"
        upcoming_groups.setdefault(date_key, []).append(ev)

    # Group past events by date
    past_groups = {}
    for ev in past_events:
        dt = ev["start_utc"] or ""
        date_key = dt[:10] if len(dt) >= 10 else "TBD"
        past_groups.setdefault(date_key, []).append(ev)

    # Sort groups by date (oldest first)
    sorted_upcoming = dict(sorted(upcoming_groups.items(),
                                  key=lambda x: x[0] if x[0] != "TBD" else "9999-12-31"))
    sorted_past = dict(sorted(past_groups.items(),
                              key=lambda x: x[0] if x[0] != "TBD" else "9999-12-31"))

    return render(
        request,
        "calendar/calendar_overview.html",
        {
            "upcoming_groups": sorted_upcoming,
            "past_groups": sorted_past,
        },
    )
def event_detail(request, event_uri):
    """
    Render the detail page for a single calendar event.
    
    Fetches event details by `event_uri`, formats fields for display, and returns a response rendering the event detail template.
    
    Parameters:
        event_uri (str): The event identifier/URI used to retrieve event details.
    
    Returns:
        HttpResponse: The rendered "calendar/event_detail.html" page containing the event data.
    
    Raises:
        Http404: If the event cannot be retrieved or no event data is returned.
    """
    try:
        event_data = presence.get_event_details(event_uri)
    except Exception as exc:
        raise Http404("Event not found") from exc

    if not event_data:
        raise Http404("Event not found")

    # Format event data for display
    event = {
        "name": event_data.get("eventName", "Untitled Event"),
        "org": event_data.get("organizationName", "Unknown Organization"),
        "location": event_data.get("location", "Location TBD"),
        "start_formatted": _format_datetime(event_data.get("startDateTimeUtc")),
        "end_formatted": _format_datetime(event_data.get("endDateTimeUtc")),
        "description": event_data.get("description", ""),
        "description_text": _safe_text(event_data.get("description", "")),
        "tags": event_data.get("tags", []),
        "uri": event_data.get("uri"),
        "contact_email": event_data.get("contactEmail"),
        "contact_phone": event_data.get("contactPhone"),
        "registration_url": event_data.get("registrationUrl"),
        "external_url": event_data.get("externalUrl"),
        "capacity": event_data.get("capacity"),
        "cost": event_data.get("cost"),
        "event_type": event_data.get("eventType"),
    }

    return render(
        request,
        "calendar/event_detail.html",
        {
            "event": event,
        },
    )