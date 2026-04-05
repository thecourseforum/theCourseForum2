"""Utility helpers shared across the Django app."""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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


def semesters_for_course(course: Course) -> QuerySet:
    """Recent-catalog semesters in which ``course`` has at least one section, newest first."""
    return (
        recent_semesters().filter(section__course=course).distinct().order_by("-number")
    )


def parse_mode(request):
    """Parse the mode parameter from the request."""
    mode = request.GET.get("mode", "courses")
    return mode, (mode == "clubs")


def update_query_params(url: str, **overrides) -> str:
    """Return ``url`` with query params added, replaced, or removed."""
    split_url = urlsplit(url)
    params = dict(parse_qsl(split_url.query, keep_blank_values=True))

    for key, value in overrides.items():
        if value in (None, ""):
            params.pop(key, None)
            continue
        params[key] = str(value)

    query = urlencode(params, doseq=True)
    return urlunsplit(
        (
            split_url.scheme,
            split_url.netloc,
            split_url.path,
            query,
            split_url.fragment,
        )
    )


def with_mode(url: str, mode: str | None) -> str:
    """Return ``url`` with the current non-default mode encoded in the querystring."""
    if mode in (None, "", "courses"):
        return update_query_params(url, mode=None)
    return update_query_params(url, mode=mode)


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
