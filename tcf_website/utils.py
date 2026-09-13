"""Utility helpers shared across the Django app."""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.db.models import Case, IntegerField, Q, QuerySet, Value, When
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .models import CATALOG_YEAR_WINDOW, Course, Semester


def min_catalog_semester_year() -> int:
    """First calendar year (inclusive) shown in the course catalog."""
    return timezone.now().year - CATALOG_YEAR_WINDOW


def browsable_course_queryset():
    """Visible catalog courses with stats annotated for display in cards."""
    return (
        Course.with_stats()
        .filter(Q(number__isnull=True) | Q(number__range=(1000, 9999)))
        .filter(semester_last_taught__year__gte=min_catalog_semester_year())
    )


def recent_semesters() -> QuerySet:
    """Semesters in the catalog year window, newest SIS number first."""
    return Semester.objects.filter(year__gte=min_catalog_semester_year()).order_by(
        "-number"
    )


def reviewable_semesters() -> QuerySet:
    """Recent-catalog semesters that have already started, so a course can only
    be reviewed for a term that has actually happened (never a future term that
    is merely loaded for course registration)."""
    now = timezone.now()
    start_month = Case(
        *[
            When(season=season, then=Value(month))
            for season, month in Semester.SEASON_START_MONTH.items()
        ],
        default=Value(12),
        output_field=IntegerField(),
    )
    return (
        recent_semesters()
        .annotate(start_month=start_month)
        .filter(Q(year__lt=now.year) | Q(year=now.year, start_month__lte=now.month))
    )


def semesters_for_course(course: Course) -> QuerySet:
    """Started recent-catalog semesters in which ``course`` has at least one section, newest first."""
    return (
        reviewable_semesters()
        .filter(section__course=course)
        .distinct()
        .order_by("-number")
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
    """Round num to 2 decimal places; returns None when value is missing."""
    if num is not None:
        return round(num, 2)
    return None


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
