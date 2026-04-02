"""Browse landing page (course catalog vs clubs) and advanced search queryset."""

from django.db.models import Exists, F, OuterRef, Prefetch, Q
from django.http import HttpResponse
from django.shortcuts import render

from ..forms import AdvancedSearchForm
from ..models import Club, ClubCategory, School, Section, Semester
from ..pagination import SECTION_DAY_CODE_TO_SECTIONTIME_FIELD, paginate
from ..utils import browsable_course_queryset, parse_mode
from .search import course_to_row_dict, group_by_dept


def execute_advanced_search(filters):
    """Build and execute advanced search queryset from validated form data."""
    qs = browsable_course_queryset()
    qs = _apply_course_filters(qs, filters)
    qs = _apply_section_filters(qs, filters)
    return qs.distinct().order_by("subdepartment__mnemonic", "number")


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

    if min_gpa := filters.get("min_gpa"):
        section_q &= Q(
            section__instructors__courseinstructorgrade__course_id=F("id"),
            section__instructors__courseinstructorgrade__average__gte=min_gpa,
        )

    if day_q := _days_section_q(filters.get("days", [])):
        section_q &= day_q

    if start_time := filters.get("start_time"):
        section_q &= Q(section__sectiontime__start_time__gte=start_time)

    if end_time := filters.get("end_time"):
        section_q &= Q(section__sectiontime__end_time__lte=end_time)

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


def _is_browse_results_partial_request(request) -> bool:
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        and request.GET.get("partial") == "results"
    )


def _advanced_search_results_payload(request, form: AdvancedSearchForm) -> dict:
    """Run advanced search for a bound valid form with search params."""
    results = execute_advanced_search(form.cleaned_data)
    page_obj = paginate(results, request.GET.get("page", 1), per_page=15)
    total = page_obj.paginator.count
    courses = [course_to_row_dict(c) for c in page_obj]
    grouped = group_by_dept(courses)
    return {
        "grouped": grouped,
        "page_obj": page_obj,
        "total": total,
    }


def browse(request):  # pylint: disable=too-many-locals
    """View for browse page with advanced course search."""
    mode, is_club = parse_mode(request)

    if is_club:
        club_categories = (
            ClubCategory.objects.all()
            .prefetch_related(
                Prefetch(
                    "club_set",
                    queryset=Club.objects.order_by("name"),
                    to_attr="clubs",
                )
            )
            .order_by("name")
        )

        return render(
            request,
            "site/pages/browse.html",
            {
                "is_club": True,
                "mode": mode,
                "club_categories": club_categories,
            },
        )

    form = AdvancedSearchForm(request.GET or None)
    has_search = form.is_bound and form.has_search_params()

    if _is_browse_results_partial_request(request):
        if not has_search:
            return HttpResponse(status=204)
        payload = _advanced_search_results_payload(request, form)
        return render(
            request,
            "site/partials/_browse_advanced_results.html",
            {"request": request, **payload},
        )

    if has_search:
        payload = _advanced_search_results_payload(request, form)
        return render(
            request,
            "site/pages/browse.html",
            {
                "is_club": False,
                "mode": mode,
                "form": form,
                "has_search": True,
                **payload,
            },
        )

    featured = {
        s.name: s
        for s in School.objects.filter(
            name__in=[
                "College of Arts & Sciences",
                "School of Engineering & Applied Science",
            ]
        )
    }
    clas = featured["College of Arts & Sciences"]
    seas = featured["School of Engineering & Applied Science"]

    excluded_list = [clas.pk, seas.pk]
    other_schools = School.objects.exclude(pk__in=excluded_list).order_by("name")

    return render(
        request,
        "site/pages/browse.html",
        {
            "is_club": False,
            "mode": mode,
            "form": form if form.is_bound else AdvancedSearchForm(),
            "has_search": False,
            "CLAS": clas,
            "SEAS": seas,
            "other_schools": other_schools,
        },
    )
