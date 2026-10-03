"""Utility helpers shared across the Django app."""

from datetime import date
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.db.models import Q, QuerySet
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .models import CATALOG_YEAR_WINDOW, Course, Semester

_SEASON_CODES = {"fall": "8", "summer": "6", "spring": "2", "january": "1"}


def sis_term_code(semester: str) -> str | None:
    """Return the SIS term for ``<year>_<season>``, or None when it is invalid.

    2026_fall is 1268: century digit 1, two-digit year, then the season digit.
    """
    year, separator, season = semester.partition("_")
    code = _SEASON_CODES.get(season.lower())
    if separator != "_" or len(year) != 4 or not year.isdigit() or code is None:
        return None
    if "_" in season:
        return None
    return f"1{year[-2:]}{code}"


# First day of courses, from https://registrar.virginia.edu/calendar/academic
# through Spring 2030. Keep this tuple identical to tCF-data/fetch_page.py.
# The 2027-2028 and 2028-2029 pages omit some labels; those starts are the
# dates in the courses-begin position. Summer 2026 and 2027 are the first
# Summer Session class day; those registrar pages do not list one.
_SEMESTER_STARTS = (
    (date(2025, 8, 26), "2025_fall"),
    (date(2026, 1, 2), "2026_january"),
    (date(2026, 1, 12), "2026_spring"),
    (date(2026, 5, 18), "2026_summer"),
    (date(2026, 8, 25), "2026_fall"),
    (date(2027, 1, 4), "2027_january"),
    (date(2027, 1, 20), "2027_spring"),
    (date(2027, 5, 17), "2027_summer"),
    (date(2027, 8, 24), "2027_fall"),
    (date(2028, 1, 3), "2028_january"),
    (date(2028, 1, 19), "2028_spring"),
    (date(2028, 8, 22), "2028_fall"),
    (date(2029, 1, 2), "2029_january"),
    (date(2029, 1, 15), "2029_spring"),
    (date(2029, 8, 21), "2029_fall"),
    (date(2030, 1, 2), "2030_january"),
    (date(2030, 1, 14), "2030_spring"),
)
_PUBLISHED_SEMESTERS = {name for _, name in _SEMESTER_STARTS}
_SEASON_ORDER = {"january": 1, "spring": 2, "summer": 3, "fall": 4}


def _semester_key(name: str) -> tuple[int, int]:
    year, _, season = name.partition("_")
    return int(year), _SEASON_ORDER[season]


def _general_semester(today: date) -> str:
    """Seasons with no published start. January 2, January 15, May 18, August 25.

    ponytail: these four days stand in for years the registrar has not posted,
    and for summers after 2027. Upgrade path: add a row to _SEMESTER_STARTS.
    """
    if today.month == 1 and today.day == 1:
        return f"{today.year - 1}_fall"
    if today.month == 1 and today.day < 15:
        return f"{today.year}_january"
    if today.month < 5 or (today.month == 5 and today.day < 18):
        return f"{today.year}_spring"
    if today.month < 8 or (today.month == 8 and today.day < 25):
        return f"{today.year}_summer"
    return f"{today.year}_fall"


def current_semester(today: date | None = None) -> str:
    """Return ``<year>_<season>`` for a calendar date."""
    today = date.today() if today is None else today
    chosen = None
    for start, name in _SEMESTER_STARTS:
        if today < start:
            break
        chosen = name
    general = _general_semester(today)
    if chosen is None or (
        general not in _PUBLISHED_SEMESTERS and _semester_key(general) > _semester_key(chosen)
    ):
        return general
    return chosen


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
