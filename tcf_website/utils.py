"""Utility helpers shared across the Django app."""

from django.db.models import F, Q, QuerySet
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Course, Semester

# Rolling window for catalog browse/search and term pickers (calendar years).
_CATALOG_YEAR_WINDOW = 5


def _min_catalog_semester_year() -> int:
    """First calendar year (inclusive) to show in the course catalog."""
    return timezone.now().year - _CATALOG_YEAR_WINDOW


def browsable_course_queryset():
    """Visible catalog courses: subdepartment join, mnemonic, number range, recency."""

    return (
        Course.objects.select_related("subdepartment")
        .only("title", "number", "subdepartment__mnemonic", "description")
        .annotate(mnemonic=F("subdepartment__mnemonic"))
        .filter(Q(number__isnull=True) | Q(number__range=(1000, 9999)))
        .filter(semester_last_taught__year__gte=_min_catalog_semester_year())
    )


def recent_semesters() -> QuerySet:
    """Semesters in the catalog year window, newest SIS number first."""
    return Semester.objects.filter(year__gte=_min_catalog_semester_year()).order_by(
        "-number"
    )


def parse_mode(request):
    """Parse the mode parameter from the request."""
    mode = request.GET.get("mode", "courses")
    return mode, (mode == "clubs")


def safe_round(num):
    """Reduce repetition for null-checked rounding; returns an em dash when value is missing."""
    if num is not None:
        return round(num, 2)
    return "\u2014"


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
