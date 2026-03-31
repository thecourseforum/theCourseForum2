"""Browse landing page (course catalog vs clubs) and advanced search queryset."""

from django.db.models import Exists, F, OuterRef, Prefetch, Q
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


def _apply_section_filters(qs, filters):
    """Apply section-level filters in one Q so joins refer to the same Section row."""
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

    if days := filters.get("days", []):
        day_q = Q()
        for day_code in days:
            if day_code in SECTION_DAY_CODE_TO_SECTIONTIME_FIELD:
                field = SECTION_DAY_CODE_TO_SECTIONTIME_FIELD[day_code]
                day_q |= Q(**{f"section__sectiontime__{field}": True})
        if day_q:
            section_q &= day_q

    if start_time := filters.get("start_time"):
        section_q &= Q(section__sectiontime__start_time__gte=start_time)

    if end_time := filters.get("end_time"):
        section_q &= Q(section__sectiontime__end_time__lte=end_time)

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

    if has_search:
        results = execute_advanced_search(form.cleaned_data)
        page_obj = paginate(results, request.GET.get("page", 1), per_page=15)
        total = page_obj.paginator.count

        courses = [course_to_row_dict(c) for c in page_obj]
        grouped = group_by_dept(courses)

        return render(
            request,
            "site/pages/browse.html",
            {
                "is_club": False,
                "mode": mode,
                "form": form,
                "has_search": True,
                "grouped": grouped,
                "total": total,
                "page_obj": page_obj,
            },
        )

    featured = {
        s.name: s
        for s in School.objects.filter(
            name__in=["College of Arts & Sciences", "School of Engineering & Applied Science"]
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
