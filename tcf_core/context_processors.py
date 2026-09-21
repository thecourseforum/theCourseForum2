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
    """After finals, tell signed-in users how many past courses they can rate."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}
    if timezone.now().month not in settings.QUICK_RATE_BANNER_MONTHS:
        return {}
    if request.path.startswith(reverse("quick_rate")):
        return {}
    return {"quick_rate_banner_count": len(candidates_for(user))}
