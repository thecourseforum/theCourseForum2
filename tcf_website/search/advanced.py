"""Advanced course search queryset (browse page filters)."""

from django.db.models import Exists, F, OuterRef, Q

from ..models import Club, Section, Semester
from ..pagination import SECTION_DAY_CODE_TO_SECTIONTIME_FIELD
from ..utils import browsable_course_queryset

_SORT_MAP = {
    "rating_desc": F("average_rating").desc(nulls_last=True),
    "gpa_desc": F("average_gpa").desc(nulls_last=True),
    "difficulty_asc": F("average_difficulty").asc(nulls_last=True),
}

_DEFAULT_ORDER = ("subdepartment__mnemonic", "number")


def execute_advanced_search(filters):
    """Build and execute advanced search queryset from validated form data."""
    qs = browsable_course_queryset()
    qs = _apply_course_filters(qs, filters)
    qs = _apply_section_filters(qs, filters)
    sort_expr = _SORT_MAP.get(filters.get("sort") or "")
    if sort_expr is not None:
        # Primary sort by chosen field; tiebreak by dept/number for stable grouping.
        return qs.distinct().order_by(sort_expr, *_DEFAULT_ORDER)
    return qs.distinct().order_by(*_DEFAULT_ORDER)


def execute_club_advanced_search(filters):
    """Build club queryset from validated club browse form data."""
    qs = Club.objects.select_related("category").order_by("category__name", "name")
    club_q = Q()
    if category := filters.get("category"):
        club_q &= Q(category_id=category)
    if name := (filters.get("club_name") or "").strip():
        club_q &= Q(name__icontains=name)
    if filters.get("no_application_required"):
        club_q &= Q(application_required=False)
    if club_q:
        qs = qs.filter(club_q)
    return qs


def _apply_course_filters(qs, filters):
    """Apply course-level filters in one Q."""
    course_q = Q()

    if school := filters.get("school"):
        course_q &= Q(subdepartment__department__school_id=school)

    if subject := filters.get("subject"):
        course_q &= Q(subdepartment__mnemonic=subject)

    if course_number := filters.get("course_number"):
        course_q &= Q(number__startswith=course_number)

    if title := filters.get("title"):
        course_q &= Q(title__icontains=title)

    if description := filters.get("description"):
        course_q &= Q(description__icontains=description)

    if discipline := filters.get("discipline"):
        course_q &= Q(disciplines__name__in=discipline)

    if course_q:
        qs = qs.filter(course_q)

    return qs


def _units_section_filter(filters):
    """Parse units_min/units_max from filter dict.

    Returns (empty_result, q):
      empty_result True → caller should use qs.none();
      otherwise AND q into section_q when q is not None.
    """

    def _parse_bound(key):
        raw = str(filters.get(key) or "").strip()
        if not raw:
            return None
        try:
            return int(round(float(raw)))
        except ValueError:
            return None

    lo = _parse_bound("units_min")
    hi = _parse_bound("units_max")
    if lo is None and hi is None:
        return False, None
    if lo is not None and hi is not None and lo > hi:
        return True, None
    if lo is not None and hi is not None:
        return False, Q(section__units_max__gte=lo) & Q(section__units_min__lte=hi)
    if lo is not None:
        return False, Q(section__units_max__gte=lo)
    return False, Q(section__units_min__lte=hi)


def _days_section_q(day_codes):
    """OR day-of-week flags on section times; None if nothing to constrain."""
    if not day_codes:
        return None
    day_q = Q()
    matched = False
    for code in day_codes:
        field = SECTION_DAY_CODE_TO_SECTIONTIME_FIELD.get(code)
        if field:
            matched = True
            day_q |= Q(**{f"section__sectiontime__{field}": True})
    return day_q if matched else None


def _section_filters_query(filters):
    """Build combined section Q; returns (query, units_impossible)."""
    section_q = Q()

    if semester := filters.get("semester"):
        section_q &= Q(section__semester_id=semester)

    if component := filters.get("component"):
        section_q &= Q(section__section_type__icontains=component)

    if instructor := filters.get("instructor"):
        section_q &= Q(section__instructors__full_name__icontains=instructor)

    if day_q := _days_section_q(filters.get("days", [])):
        section_q &= day_q

    if start_time := filters.get("start_time"):
        section_q &= Q(section__sectiontime__start_time__gte=start_time)

    if end_time := filters.get("end_time"):
        section_q &= Q(section__sectiontime__end_time__lte=end_time)

    if min_gpa := filters.get("min_gpa"):
        section_q &= Q(
            section__instructors__courseinstructorgrade__course_id=F("id"),
            section__instructors__courseinstructorgrade__average__gte=min_gpa,
        )

    empty, units_q = _units_section_filter(filters)
    if empty:
        return None, True
    if units_q is not None:
        section_q &= units_q

    return section_q, False


def _apply_section_filters(qs, filters):
    """Apply section-level filters in one Q so joins refer to the same Section row."""
    section_q, units_impossible = _section_filters_query(filters)
    if units_impossible:
        return qs.none()

    if section_q:
        qs = qs.filter(section_q)

    if filters.get("open_sections"):
        open_sec = Section.objects.filter(
            course=OuterRef("pk"),
            semester=Semester.latest(),
            enrollment_taken__lt=F("enrollment_limit"),
        )
        qs = qs.filter(Exists(open_sec))

    return qs
