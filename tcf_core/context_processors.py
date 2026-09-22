"""Inject extra context to TCF templates."""

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from tcf_website.models import Semester
from tcf_website.review.quick_rate import QUICK_RATE_BANNER_SESSION_KEY, candidates_for


def base(request):
    """Inject user + latest semester info."""
    return {
        "DEBUG": settings.DEBUG,
        "USER": request.user,
        "LATEST_SEMESTER": Semester.latest(),
    }


def _banner_count(request):
    """Today's candidate count, cached in the session so pages stay cheap."""
    session = getattr(request, "session", None)
    today = timezone.now().date().isoformat()
    if session is not None:
        cached = session.get(QUICK_RATE_BANNER_SESSION_KEY)
        if cached and cached.get("day") == today:
            return cached["count"]
    count = len(candidates_for(request.user))
    if session is not None:
        session[QUICK_RATE_BANNER_SESSION_KEY] = {"day": today, "count": count}
    return count


def quick_rate_banner(request):
    """After finals, tell signed-in users how many past courses they can rate.

    Silent on the quick-rate page itself (nothing to prompt) and on the
    schedule page, which already shows its own quick-rate card — otherwise
    both would stack, and the schedule page would end up running
    ``candidates_for`` twice per request. The count itself is cached in the
    session for the day, so pages stay cheap in banner months.
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}
    if timezone.now().month not in settings.QUICK_RATE_BANNER_MONTHS:
        return {}
    if request.path.startswith(reverse("quick_rate")) or request.path == reverse(
        "schedule"
    ):
        return {}
    return {"quick_rate_banner_count": _banner_count(request)}
