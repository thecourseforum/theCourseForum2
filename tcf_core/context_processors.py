"""Inject extra context to TCF templates."""

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from tcf_website.models import Semester
from tcf_website.review.quick_rate import candidates_for


def base(request):
    """Inject user + latest semester info."""
    return {
        "DEBUG": settings.DEBUG,
        "USER": request.user,
        "LATEST_SEMESTER": Semester.latest(),
    }


def quick_rate_banner(request):
    """After finals, tell signed-in users how many past courses they can rate.

    Silent on the quick-rate page itself (nothing to prompt) and on the
    schedule page, which already shows its own quick-rate card — otherwise
    both would stack, and the schedule page would end up running
    ``candidates_for`` twice per request.
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}
    if timezone.now().month not in settings.QUICK_RATE_BANNER_MONTHS:
        return {}
    if request.path.startswith(reverse("quick_rate")) or request.path.startswith(
        reverse("schedule")
    ):
        return {}
    return {"quick_rate_banner_count": len(candidates_for(user))}
