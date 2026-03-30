# pylint disable=bad-continuation
# pylint: disable=too-many-locals

"""Views for Browse, department, and course/course instructor pages."""
import json
from typing import Any

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Avg, Count, F, Prefetch, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ..forms import AdvancedSearchForm
from ..models import (
    Club,
    ClubCategory,
    Course,
    CourseInstructorGrade,
    Department,
    Instructor,
    Review,
    School,
    Section,
    Semester,
)
from .search import group_by_dept, paginate_results


def browse(request):
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
        results = _execute_advanced_search(form.cleaned_data)
        page_obj, total = paginate_results(request, results)

        courses = [
            {
                "id": c.id,
                "title": c.title,
                "number": c.number,
                "mnemonic": c.mnemonic,
                "description": c.description,
            }
            for c in page_obj
        ]
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

    clas = School.objects.get(name="College of Arts & Sciences")
    seas = School.objects.get(name="School of Engineering & Applied Science")

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


def _execute_advanced_search(filters):
    """Build and execute advanced search queryset from validated form data."""
    qs = (
        Course.objects.select_related("subdepartment")
        .only("title", "number", "subdepartment__mnemonic", "description")
        .annotate(mnemonic=F("subdepartment__mnemonic"))
        .filter(Q(number__isnull=True) | Q(number__regex=r"^\d{4}$"))
        .exclude(semester_last_taught_id__lt=48)
    )

    qs = _apply_course_filters(qs, filters)
    qs = _apply_section_filters(qs, filters)

    return qs.distinct().order_by("subdepartment__mnemonic", "number")


def _apply_course_filters(qs, filters):
    """Apply course-level filters (school, subject, title, etc.)."""
    if filters.get("school"):
        qs = qs.filter(subdepartment__department__school_id=filters["school"])

    if filters.get("subject"):
        qs = qs.filter(subdepartment__mnemonic=filters["subject"])

    if filters.get("course_number"):
        qs = qs.filter(number__startswith=filters["course_number"])

    if filters.get("title"):
        qs = qs.filter(title__icontains=filters["title"])

    if filters.get("description"):
        qs = qs.filter(description__icontains=filters["description"])

    if filters.get("discipline"):
        qs = qs.filter(disciplines__name__in=filters["discipline"])

    if filters.get("level"):
        level = int(filters["level"])
        if level < 5:
            qs = qs.filter(number__gte=level * 1000, number__lt=(level + 1) * 1000)
        else:
            qs = qs.filter(number__gte=5000)

    if filters.get("min_gpa"):
        qs = qs.filter(coursegrade__average__gte=filters["min_gpa"])

    return qs


def _apply_section_filters(qs, filters):
    """Apply section-level filters (semester, instructor, days, time, etc.)."""
    if filters.get("semester"):
        qs = qs.filter(section__semester_id=filters["semester"])

    if filters.get("component"):
        qs = qs.filter(section__section_type__icontains=filters["component"])

    if filters.get("instructor"):
        qs = qs.filter(section__instructors__full_name__icontains=filters["instructor"])

    if filters.get("open_sections"):
        open_ids = Course.filter_by_open_sections().values_list("id", flat=True)
        qs = qs.filter(id__in=open_ids)

    # Day filter: show courses that MEET on the selected days
    #pylint: disable=duplicate-code
    day_map = {
        "MON": "monday",
        "TUE": "tuesday",
        "WED": "wednesday",
        "THU": "thursday",
        "FRI": "friday",
    }
    days = filters.get("days", [])
    if days:
        day_q = Q()
        for day_code in days:
            if day_code in day_map:
                day_q |= Q(**{f"section__sectiontime__{day_map[day_code]}": True})
        qs = qs.filter(day_q)

    if filters.get("start_time"):
        qs = qs.filter(section__sectiontime__start_time__gte=filters["start_time"])
    if filters.get("end_time"):
        qs = qs.filter(section__sectiontime__end_time__lte=filters["end_time"])

    return qs


def department(request, dept_id: int, course_recency=None):
    """View for department page - Modern design."""
    dept = get_object_or_404(
        Department.objects.prefetch_related("subdepartment_set"), pk=dept_id
    )

    if not course_recency:
        course_recency = str(Semester.latest())

    breadcrumbs = [
        (dept.school.name, reverse("browse"), False),
        (dept.name, None, True),
    ]

    latest_semester = Semester.latest()
    last_five_years = get_object_or_404(Semester, number=latest_semester.number - 50)
    season, year = course_recency.upper().split()
    active_semester = Semester.objects.filter(year=year, season=season).first()

    sortby = request.GET.get("sortby", "course_id")
    order = request.GET.get("order", "asc")
    page = request.GET.get("page", 1)

    paginated_courses = dept.get_paginated_department_courses(
        sortby, latest_semester.year - int(year), order, page
    )

    return render(
        request,
        "site/pages/department.html",
        {
            "dept_id": dept_id,
            "latest_semester": str(latest_semester),
            "breadcrumbs": breadcrumbs,
            "paginated_courses": paginated_courses,
            "active_course_recency": str(active_semester),
            "sortby": sortby,
            "order": order,
            "last_five_years": str(last_five_years),
        },
    )


def parse_mode(request):
    """Parse the mode parameter from the request."""
    mode = request.GET.get("mode", "courses")
    return mode, (mode == "clubs")


def _is_lecture_section(section_type: str | None) -> bool:
    """Return True when a section type should be treated as lecture."""
    if not section_type:
        return True
    normalized = section_type.strip().lower()
    return normalized.startswith("lec")


def _split_section_times(section_times: str) -> list[str]:
    """Convert comma-separated section times into a clean list."""
    if not section_times:
        return []
    return [
        entry.strip() for entry in section_times.rstrip(",").split(",") if entry.strip()
    ]


def _build_section_times_maps_by_instructor(
    course_id: int, semester: Semester
) -> tuple[dict[int, dict[str, list[str]]], dict[int, dict[str, list[str]]]]:
    """Build all-sections and lecture-only section-time maps keyed by instructor ID."""
    all_times_by_instructor: dict[int, dict[str, list[str]]] = {}
    lecture_times_by_instructor: dict[int, dict[str, list[str]]] = {}

    sections = (
        Section.objects.filter(course_id=course_id, semester=semester)
        .prefetch_related("instructors")
        .order_by("sis_section_number")
    )

    for section in sections:
        times = _split_section_times(section.section_times)
        if not times:
            continue

        section_number = str(section.sis_section_number)
        for section_instructor in section.instructors.all():
            all_times_by_instructor.setdefault(section_instructor.id, {})[
                section_number
            ] = times
            if _is_lecture_section(section.section_type):
                lecture_times_by_instructor.setdefault(section_instructor.id, {})[
                    section_number
                ] = times

    return all_times_by_instructor, lecture_times_by_instructor


def _get_paginated_club_reviews(club: Club, user, page_number=1, method=""):
    """Build sorted/paginated club reviews with vote annotations."""
    reviews = Review.objects.filter(
        club=club,
        toxicity_rating__lt=settings.TOXICITY_THRESHOLD,
        hidden=False,
    ).exclude(text="")

    if user.is_authenticated:
        reviews = reviews.annotate(
            sum_votes=Coalesce(Sum("vote__value"), Value(0)),
            user_vote=Coalesce(
                Sum("vote__value", filter=Q(vote__user=user)),
                Value(0),
            ),
        )

    return Review.paginate(Review.sort(reviews, method), page_number)


def _build_club_page_context(request, club: Club, mode: str):
    """Build shared context for club detail pages."""
    sort_method = request.GET.get("sort", "")
    page_number = request.GET.get("page", 1)
    paginated_reviews = _get_paginated_club_reviews(
        club, request.user, page_number, sort_method
    )

    breadcrumbs = [
        ("Clubs", reverse("browse") + "?mode=clubs", False),
        (
            club.category.name,
            reverse("club_category", args=[club.category.slug]) + "?mode=clubs",
            False,
        ),
        (club.name, None, True),
    ]

    return {
        "is_club": True,
        "mode": mode,
        "club": club,
        "paginated_reviews": paginated_reviews,
        "num_reviews": paginated_reviews.paginator.count,
        "sort_method": sort_method,
        "breadcrumbs": breadcrumbs,
        "course_code": f"{club.category.slug} {club.id}",
        "course_title": club.name,
    }


def course_view(request, mnemonic: str, course_number: int, instructor_recency=None):
    """Course view."""
    if mnemonic != mnemonic.upper():
        return redirect(
            "course", mnemonic=mnemonic.upper(), course_number=course_number
        )

    course = get_object_or_404(
        Course,
        subdepartment__mnemonic=mnemonic.upper(),
        number=course_number,
    )

    latest_semester = Semester.latest()
    show_all = request.GET.get("show") == "all"
    if not instructor_recency:
        instructor_recency = str(latest_semester)
    recent = not show_all and str(latest_semester) == instructor_recency

    sortby = request.GET.get("sortby", "last_taught")
    order = request.GET.get("order", "desc")

    instructors = course.sort_instructors_by_key(latest_semester, recent, order, sortby)

    for instructor in instructors:
        if hasattr(instructor, "section_times") and instructor.section_times:
            instructor.section_times = [
                s for s in instructor.section_times if s is not None
            ]
        if hasattr(instructor, "section_nums") and instructor.section_nums:
            instructor.section_nums = [
                s for s in instructor.section_nums if s is not None
            ]

    all_times_by_instructor, lecture_times_by_instructor = (
        _build_section_times_maps_by_instructor(course.id, latest_semester)
    )

    for instructor in instructors:
        instructor.semester_last_taught = str(
            get_object_or_404(Semester, pk=instructor.semester_last_taught)
        )
        instructor.times = lecture_times_by_instructor.get(instructor.id, {})
        instructor.all_times = all_times_by_instructor.get(instructor.id, {})

    dept = course.subdepartment.department

    breadcrumbs = [
        (dept.school.name, reverse("browse"), False),
        (dept.name, reverse("department", args=[dept.pk]), False),
        (course.code, None, True),
    ]

    return render(
        request,
        "site/pages/course.html",
        {
            "course": course,
            "instructors": instructors,
            "latest_semester": str(latest_semester),
            "breadcrumbs": breadcrumbs,
            "sortby": sortby,
            "order": order,
            "active_instructor_recency": "all_time" if show_all else instructor_recency,
            "course_code": course.code(),
            "course_title": course.title,
            "all_section_times_by_instructor": all_times_by_instructor,
        },
    )


def course_instructor(request, course_id, instructor_id, method="Default"):
    """Course-instructor view."""
    section_last_taught = (
        Section.objects.filter(course_id=course_id, instructors__id=instructor_id)
        .order_by("-semester__number")
        .select_related("course", "semester")
        .prefetch_related("instructors")
        .first()
    )
    if section_last_taught is None:
        raise Http404
    course = section_last_taught.course
    instructor = section_last_taught.instructors.get(pk=instructor_id)

    reviews = Review.objects.filter(
        instructor=instructor_id,
        course=course_id,
        toxicity_rating__lt=settings.TOXICITY_THRESHOLD,
    ).aggregate(num_ratings=Count("id"), num_reviews=Count("id", filter=~Q(text="")))
    num_reviews, num_ratings = reviews["num_reviews"], reviews["num_ratings"]

    dept = course.subdepartment.department

    sort_method = request.GET.get("sort", method)
    page_number = request.GET.get("page", 1)
    paginated_reviews = Review.get_paginated_reviews(
        course_id, instructor_id, request.user, page_number, sort_method
    )

    course_url = reverse("course", args=[course.subdepartment.mnemonic, course.number])
    breadcrumbs = [
        (dept.school.name, reverse("browse"), False),
        (dept.name, reverse("department", args=[dept.pk]), False),
        (course.code, course_url, False),
        (instructor.full_name, None, True),
    ]

    data = Review.objects.filter(course=course_id, instructor=instructor_id).aggregate(
        average_rating=(
            Avg("instructor_rating") + Avg("enjoyability") + Avg("recommendability")
        )
        / 3,
        instructor=Avg("instructor_rating"),
        enjoyability=Avg("enjoyability"),
        difficulty=Avg("difficulty"),
        recommendability=Avg("recommendability"),
        hours=Avg("hours_per_week"),
        amount_reading=Avg("amount_reading"),
        amount_writing=Avg("amount_writing"),
        amount_group=Avg("amount_group"),
        amount_homework=Avg("amount_homework"),
    )
    for key, value in data.items():
        if value is not None:
            data[key] = round(value, 2)

    try:
        grades_data = CourseInstructorGrade.objects.get(
            instructor=instructor, course=course
        )
    except ObjectDoesNotExist:
        pass
    else:
        data["average_gpa"] = (
            round(grades_data.average, 2) if grades_data.average else None
        )
        fields = [
            "a_plus",
            "a",
            "a_minus",
            "b_plus",
            "b",
            "b_minus",
            "c_plus",
            "c",
            "c_minus",
            "dfw",
            "total_enrolled",
        ]
        for field in fields:
            data[field] = getattr(grades_data, field)

    latest_semester = Semester.latest()
    is_current_semester = section_last_taught.semester.number == latest_semester.number

    lecture_sections = []
    other_sections = []
    if is_current_semester:
        sections_qs = Section.objects.filter(
            course_id=course_id, instructors__id=instructor_id, semester=latest_semester
        ).order_by("sis_section_number")

        for section in sections_qs:
            times_display = ""
            if section.section_times:
                times_display = section.section_times.rstrip(",")

            section_data = {
                "number": section.sis_section_number,
                "type": section.section_type or "Section",
                "units": section.units,
                "times": times_display,
                "enrollment_taken": section.enrollment_taken or 0,
                "enrollment_limit": section.enrollment_limit or 0,
                "waitlist_taken": section.waitlist_taken or 0,
                "waitlist_limit": section.waitlist_limit or 0,
            }
            if _is_lecture_section(section.section_type):
                lecture_sections.append(section_data)
            else:
                other_sections.append(section_data)

    return render(
        request,
        "site/pages/course_instructor.html",
        {
            "course": course,
            "course_id": course_id,
            "instructor": instructor,
            "semester_last_taught": section_last_taught.semester,
            "num_ratings": num_ratings,
            "num_reviews": num_reviews,
            "paginated_reviews": paginated_reviews,
            "breadcrumbs": breadcrumbs,
            "data": json.dumps(data),
            "display_times": latest_semester == section_last_taught.semester,
            "is_current_semester": is_current_semester,
            "sort_method": sort_method,
            "sem_code": section_last_taught.semester.number,
            "course_code": course.code(),
            "course_title": course.title,
            "instructor_fullname": instructor.full_name,
            "lecture_sections": lecture_sections,
            "other_sections": other_sections,
            "sections_count": len(lecture_sections) + len(other_sections),
        },
    )


def instructor_view(request, instructor_id):
    """Instructor view."""
    instructor: Instructor = get_object_or_404(Instructor, pk=instructor_id)

    stats: dict[str, float] = Instructor.objects.filter(pk=instructor.pk).aggregate(
        avg_gpa=Avg("courseinstructorgrade__average"),
        avg_difficulty=Avg("review__difficulty"),
        avg_rating=(
            Avg("review__instructor_rating")
            + Avg("review__enjoyability")
            + Avg("review__recommendability")
        )
        / 3,
    )

    courses = list(instructor.get_course_summaries())
    is_teaching_current_semester = any(course.get("is_current") for course in courses)

    semester_numbers = {
        num for num in (c.get("latest_semester_number") for c in courses) if num
    }
    semester_info = {
        s["number"]: (s["season"], s["year"])
        for s in Semester.objects.filter(number__in=semester_numbers).values(
            "number", "season", "year"
        )
    }

    grouped_courses: dict[str, list[dict[str, Any]]] = {}
    for course in courses:
        course["avg_rating"] = safe_round(course["avg_rating"])
        course["avg_difficulty"] = safe_round(course["avg_difficulty"])
        course["avg_gpa"] = safe_round(course["avg_gpa"])
        sem_num = course.pop("latest_semester_number", None)
        if sem_num and sem_num in semester_info:
            season, year = semester_info[sem_num]
            course["last_taught"] = f"{season} {year}".title()
        else:
            course["last_taught"] = "—"

        grouped_courses.setdefault(course["subdepartment_name"], []).append(course)

    context: dict[str, Any] = {
        "instructor": instructor,
        **{key: safe_round(value) for key, value in stats.items()},
        "courses": grouped_courses,
        "is_teaching_current_semester": is_teaching_current_semester,
    }
    return render(request, "site/pages/instructor.html", context)


def safe_round(num):
    """Helper function to reduce syntax repetitions for null checking rounding.

    Returns — if None is passed because that's what appears on the site when there's no data.
    """
    if num is not None:
        return round(num, 2)
    return "\u2014"


def club_category(request, category_slug: str):
    """View for club category page."""
    mode = "clubs"
    category = get_object_or_404(ClubCategory, slug=category_slug.upper())
    clubs = Club.objects.filter(category=category).order_by("name")

    page_number = request.GET.get("page", 1)
    paginator = Paginator(clubs, 10)
    try:
        paginated_clubs = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_clubs = paginator.page(1)
    except EmptyPage:
        paginated_clubs = paginator.page(paginator.num_pages)

    breadcrumbs = [
        ("Clubs", reverse("browse") + "?mode=clubs", False),
        (category.name, None, True),
    ]

    return render(
        request,
        "site/pages/club_category.html",
        {
            "is_club": True,
            "mode": mode,
            "category": category,
            "paginated_clubs": paginated_clubs,
            "breadcrumbs": breadcrumbs,
        },
    )


def club_view(request, category_slug: str, club_id: int):
    """View for club detail page."""
    mode = "clubs"
    club = get_object_or_404(Club, id=club_id, category__slug=category_slug.upper())
    return render(
        request,
        "site/pages/club.html",
        _build_club_page_context(request, club, mode),
    )
