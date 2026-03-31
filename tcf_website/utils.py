"""Utility helpers shared across the Django app."""

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import F, Q
from django.utils.http import url_has_allowed_host_and_scheme

# Courses/instructors taught only in semesters newer than this are shown in search.
OLDEST_VISIBLE_SEMESTER_ID = 48

# SectionTime weekday flags (forms / advanced search / Course.filter_by_time).
SECTION_DAY_CODE_TO_SECTIONTIME_FIELD = {
    "MON": "monday",
    "TUE": "tuesday",
    "WED": "wednesday",
    "THU": "thursday",
    "FRI": "friday",
}


def browsable_course_queryset():
    """Visible catalog courses: subdepartment join, mnemonic, number range, recency."""
    # Deferred import: `models` imports this module at load time (avoids circular import).
    from .models import Course  # pylint: disable=import-outside-toplevel

    return (
        Course.objects.select_related("subdepartment")
        .only("title", "number", "subdepartment__mnemonic", "description")
        .annotate(mnemonic=F("subdepartment__mnemonic"))
        .filter(Q(number__isnull=True) | Q(number__range=(1000, 9999)))
        .exclude(semester_last_taught_id__lt=OLDEST_VISIBLE_SEMESTER_ID)
    )


def parse_mode(request):
    """Parse the mode parameter from the request."""
    mode = request.GET.get("mode", "courses")
    return mode, (mode == "clubs")


def paginate(items, page_number, per_page=10):
    """Paginate a queryset or list. Returns a Page object."""
    paginator = Paginator(items, per_page)
    try:
        return paginator.page(page_number)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


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
