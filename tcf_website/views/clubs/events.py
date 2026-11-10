"""Public event list and accessible detail-page fallback."""

from itertools import groupby

from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from tcf_website.clubs.events import ClubEventFilterForm, filtered_events, public_events
from tcf_website.pagination import paginate
from tcf_website.search.browse_helpers import is_browse_results_partial_request


def _club_mode_redirect(request):
    """Return a clubs-mode redirect preserving query values, or None if canonical."""
    if request.GET.get("mode") != "clubs":
        params = request.GET.copy()
        params["mode"] = "clubs"
        return redirect(f"{request.path}?{params.urlencode()}")
    return None


@require_GET
def club_events(request):
    """Filter once, paginate occurrences, then group this page by Eastern date."""
    if response := _club_mode_redirect(request):
        return response
    form = ClubEventFilterForm(request.GET)
    page = paginate(filtered_events(form), request.GET.get("page", 1), per_page=15)
    groups = [
        (date, list(events))
        for date, events in groupby(
            page.object_list, key=lambda event: event.local_start.date()
        )
    ]
    context = {"form": form, "page_obj": page, "event_groups": groups}
    template = "site/clubs/events/list.html"
    if is_browse_results_partial_request(request):
        template = "site/clubs/events/_results.html"
    return render(request, template, context)


@require_GET
def club_event_detail(request, event_id):
    """Use the same visibility query for both normal pages and modal requests."""
    if response := _club_mode_redirect(request):
        return response
    event = get_object_or_404(public_events(), pk=event_id)
    template = "site/clubs/events/detail.html"
    if (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        and request.GET.get("partial") == "details"
    ):
        template = "site/clubs/events/_detail.html"
    return render(request, template, {"event": event})
