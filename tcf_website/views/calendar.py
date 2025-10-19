from django.conf import settings
from django.shortcuts import render
from django.utils.html import strip_tags

from tcf_website.services import presence


def _safe_text(html):
    return strip_tags(html or "").strip()


def _sort_key(evt):
    return evt.get("startDateTimeUtc") or "9999-12-31T23:59:59Z"


def calendar_overview(request):
    if not getattr(settings, "ENABLE_CLUB_CALENDAR", True):
        return render(request, "calendar/disabled.html")

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

    groups = {}
    for ev in events:
        dt = ev["start_utc"] or ""
        date_key = dt[:10] if len(dt) >= 10 else "TBD"
        groups.setdefault(date_key, []).append(ev)

    return render(
        request,
        "calendar/calendar_overview.html",
        {
            "groups": groups,
            "enable_calendar": True,
        },
    )


