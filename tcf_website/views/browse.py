# pylint disable=bad-continuation
# pylint: disable=too-many-locals

"""Views for Browse, department, and course/course instructor pages."""
import json
from typing import Any

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import (
    Avg,
    Count,
    Prefetch,
    Q,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ..models import (
    Answer,
    Club,
    ClubCategory,
    Course,
    CourseInstructorGrade,
    Department,
    Instructor,
    Question,
    Review,
    School,
    Section,
    Semester,
)


def browse(request):
    """View for browse page."""
    mode, is_club = parse_mode(request)

    if is_club:
        # Get all club categories
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
            "browse/browse.html",
            {
                "is_club": True,
                "mode": mode,
                "club_categories": club_categories,
            },
        )

    clas = School.objects.get(name="College of Arts & Sciences")
    seas = School.objects.get(name="School of Engineering & Applied Science")

    excluded_list = [clas.pk, seas.pk]

    # Other schools besides CLAS, SEAS, and Misc.
    other_schools = School.objects.exclude(pk__in=excluded_list).order_by("name")

    return render(
        request,
        "browse/browse.html",
        {
            "is_club": False,
            "mode": mode,
            "CLAS": clas,
            "SEAS": seas,
            "other_schools": other_schools,
        },
    )


def browse_v2(request):
    """V2 View for browse page - Modern design."""
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
            "v2/pages/browse.html",
            {
                "is_club": True,
                "mode": mode,
                "club_categories": club_categories,
            },
        )

    clas = School.objects.get(name="College of Arts & Sciences")
    seas = School.objects.get(name="School of Engineering & Applied Science")

    excluded_list = [clas.pk, seas.pk]
    other_schools = School.objects.exclude(pk__in=excluded_list).order_by("name")

    return render(
        request,
        "v2/pages/browse.html",
        {
            "is_club": False,
            "mode": mode,
            "CLAS": clas,
            "SEAS": seas,
            "other_schools": other_schools,
        },
    )


def department(request, dept_id: int, course_recency=None):
    """View for department page."""

    # Prefetch related subdepartments and courses to improve performance.
    # department.html loops through related subdepartments and courses.
    # See:
    # https://docs.djangoproject.com/en/3.0/ref/models/querysets/#django.db.models.query.QuerySet.prefetch_related
    dept = Department.objects.prefetch_related("subdepartment_set").get(pk=dept_id)
    # Current semester or last five years
    if not course_recency:
        course_recency = str(Semester.latest())

    # Navigation breadcrimbs
    breadcrumbs = [
        (dept.school.name, reverse("browse"), False),
        (dept.name, None, True),
    ]

    # Setting up sorting and course age variables
    latest_semester = Semester.latest()
    last_five_years = get_object_or_404(Semester, number=latest_semester.number - 50)
    # Fetch season and year (either current semester or 5 years previous)
    season, year = course_recency.upper().split()
    active_semester = Semester.objects.filter(year=year, season=season).first()

    # Fetch sorting variables
    sortby = request.GET.get("sortby", "course_id")
    order = request.GET.get("order", "asc")
    page = request.GET.get("page", 1)

    paginated_courses = dept.get_paginated_department_courses(
        sortby, latest_semester.year - int(year), order, page
    )

    return render(
        request,
        "department/department.html",
        {
            # "subdepartments": dept.subdepartment_set.all(),
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


def department_v2(request, dept_id: int, course_recency=None):
    """V2 View for department page - Modern design."""
    dept = Department.objects.prefetch_related("subdepartment_set").get(pk=dept_id)

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
        "v2/pages/department.html",
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


def course_view_legacy(request, course_id):
    """Legacy view for course page."""
    course = get_object_or_404(Course, pk=course_id)
    return redirect(
        "course",
        mnemonic=course.subdepartment.mnemonic,
        course_number=course.number,
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


def _build_club_page_context(request, club: Club, mode: str, *, v2: bool = False):
    """Build shared context for club detail pages."""
    sort_key = "sort" if v2 else "method"
    sort_method = request.GET.get(sort_key, "")
    page_number = request.GET.get("page", 1)
    paginated_reviews = _get_paginated_club_reviews(
        club, request.user, page_number, sort_method
    )

    if v2:
        breadcrumbs = [
            ("Clubs", reverse("browse") + "?mode=clubs", False),
            (
                club.category.name,
                reverse("club_category", args=[club.category.slug]),
                False,
            ),
            (club.name, None, True),
        ]
    else:
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


def course_view(
    request,
    mnemonic: str,
    course_number: int,
    instructor_recency=None,
):
    """A new Course view that allows you to input mnemonic and number instead."""

    mode, is_club = parse_mode(request)

    if not instructor_recency:
        instructor_recency = str(Semester.latest())

    # No longer storing in session - client-side storage will handle this
    # (JavaScript now handles this via localStorage)

    if is_club:
        club = get_object_or_404(
            Club, id=course_number, category__slug=mnemonic.upper()
        )
        return render(
            request,
            "club/club.html",
            _build_club_page_context(request, club, mode, v2=False),
        )

    # Redirect if the mnemonic is not all uppercase
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
    recent = str(latest_semester) == instructor_recency

    # Fetch sorting variables
    sortby = request.GET.get("sortby", "last_taught")
    order = request.GET.get("order", "desc")

    instructors = course.sort_instructors_by_key(latest_semester, recent, order, sortby)
    # Remove none values from section_times and section_nums
    # For whatever reason, it is not possible to remove None from .annotate()'s ArrayAgg() function
    for instructor in instructors:
        if hasattr(instructor, "section_times") and instructor.section_times:
            instructor.section_times = [
                s for s in instructor.section_times if s is not None
            ]

        if hasattr(instructor, "section_nums") and instructor.section_nums:
            instructor.section_nums = [
                s for s in instructor.section_nums if s is not None
            ]

    # Note: Could be simplified further

    for instructor in instructors:
        # Convert to string for templating
        instructor.semester_last_taught = str(
            get_object_or_404(Semester, pk=instructor.semester_last_taught)
        )
        if instructor.section_times and instructor.section_nums:
            if instructor.section_times[0] and instructor.section_nums[0]:
                instructor.times = {
                    num: times[:-1].split(",")
                    for num, times in zip(
                        instructor.section_nums, instructor.section_times
                    )
                    if num and times
                }

    dept = course.subdepartment.department

    # Navigation breadcrumbs
    breadcrumbs = [
        (dept.school.name, reverse("browse"), False),
        (dept.name, reverse("department", args=[dept.pk]), False),
        (course.code, None, True),
    ]

    # Pass course info to template for meta tags
    # (JavaScript will retrieve these from meta tags)

    return render(
        request,
        "course/course.html",
        {
            "is_club": False,
            "mode": mode,
            "course": course,
            "instructors": instructors,
            "latest_semester": str(latest_semester),
            "breadcrumbs": breadcrumbs,
            "sortby": sortby,
            "order": order,
            "active_instructor_recency": instructor_recency,
            "course_code": course.code(),
            "course_title": course.title,
        },
    )


def course_view_v2(request, mnemonic: str, course_number: int, instructor_recency=None):
    """V2 Course view - Modern design."""
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
        "v2/pages/course.html",
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
    """View for course instructor page."""
    section_last_taught = (
        Section.objects.filter(course=course_id, instructors=instructor_id)
        .order_by("-semester__number")
        .first()
    )
    if section_last_taught is None:
        raise Http404
    course = section_last_taught.course
    instructor = section_last_taught.instructors.get(pk=instructor_id)

    # ratings: reviews with and without text; reviews: ratings with text
    reviews = Review.objects.filter(
        instructor=instructor_id,
        course=course_id,
        toxicity_rating__lt=settings.TOXICITY_THRESHOLD,
    ).aggregate(num_ratings=Count("id"), num_reviews=Count("id", filter=~Q(text="")))
    num_reviews, num_ratings = reviews["num_reviews"], reviews["num_ratings"]

    dept = course.subdepartment.department

    page_number = request.GET.get("page", 1)
    paginated_reviews = Review.get_paginated_reviews(
        course_id, instructor_id, request.user, page_number, method
    )

    course_url = reverse("course", args=[course.subdepartment.mnemonic, course.number])
    # Navigation breadcrumbs
    breadcrumbs = [
        (dept.school.name, reverse("browse"), False),
        (dept.name, reverse("department", args=[dept.pk]), False),
        (course.code, course_url, False),
        (instructor.full_name, None, True),
    ]

    data = Review.objects.filter(course=course_id, instructor=instructor_id).aggregate(
        # rating stats
        average_rating=(
            Avg("instructor_rating") + Avg("enjoyability") + Avg("recommendability")
        )
        / 3,
        average_instructor=Avg("instructor_rating"),
        average_fun=Avg("enjoyability"),
        average_recommendability=Avg("recommendability"),
        average_difficulty=Avg("difficulty"),
        # workload stats
        average_hours_per_week=Avg("hours_per_week"),
        average_amount_reading=Avg("amount_reading"),
        average_amount_writing=Avg("amount_writing"),
        average_amount_group=Avg("amount_group"),
        average_amount_homework=Avg("amount_homework"),
    )
    data = {key: safe_round(value) for key, value in data.items()}

    try:
        grades_data = CourseInstructorGrade.objects.get(
            instructor=instructor, course=course
        )
    except ObjectDoesNotExist:  # if no data found
        pass
    # NOTE: Don't catch MultipleObjectsReturned because we want to be notified
    else:  # Fill in the data found
        # grades stats
        data["average_gpa"] = (
            round(grades_data.average, 2) if grades_data.average else None
        )
        # pylint: disable=duplicate-code
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

    # No longer storing in session
    # Course and instructor info is passed to template context for meta tags
    # Sections will be fetched via API when dropdown is expanded

    # QA Data
    questions = Question.objects.filter(course=course_id, instructor=instructor_id)
    answers = {}
    for question in questions:
        answers[question.id] = Answer.display_activity(question.id, request.user)
    questions = Question.display_activity(course_id, instructor_id, request.user)

    latest_semester = Semester.latest()
    is_current_semester = section_last_taught.semester.number == latest_semester.number

    # instructor dropdown
    other_instructors = (
        Instructor.objects.filter(
            section__course_id=course_id,
            section__semester=section_last_taught.semester,
            hidden=False,
        )
        .exclude(id=instructor_id)
        .distinct()
        .order_by("last_name")[:30]
    )

    # sections (current semester only)
    sections = []
    if is_current_semester:
        sections_qs = Section.objects.filter(
            course_id=course_id, instructors__id=instructor_id, semester=latest_semester
        ).order_by("sis_section_number")

        for section in sections_qs:
            times_display = ""
            if section.section_times:
                times_display = section.section_times.rstrip(",")

            sections.append(
                {
                    "number": section.sis_section_number,
                    "type": section.section_type or "Lecture",
                    "units": section.units,
                    "times": times_display,
                    "enrollment_taken": section.enrollment_taken or 0,
                    "enrollment_limit": section.enrollment_limit or 0,
                    "waitlist_taken": section.waitlist_taken or 0,
                    "waitlist_limit": section.waitlist_limit or 0,
                }
            )
    return render(
        request,
        "course/course_professor.html",
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
            "questions": questions,
            "answers": answers,
            "sort_method": method,
            "sem_code": section_last_taught.semester.number,
            "latest_semester_id": latest_semester.id,
            "course_code": course.code(),
            "course_title": course.title,
            "instructor_fullname": instructor.full_name,
            "other_instructors": other_instructors,
            "sections": sections,
        },
    )


def course_instructor_v2(request, course_id, instructor_id, method="Default"):
    """V2 Course-Instructor view - Modern design."""
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

    course_url = reverse(
        "course", args=[course.subdepartment.mnemonic, course.number]
    )
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
        "v2/pages/course_instructor.html",
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
    """View for instructor page, showing all their courses taught."""
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

    # Build a mapping from semester number to (season, year) in one query
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
    return render(request, "instructor/instructor.html", context)


def instructor_view_v2(request, instructor_id):
    """V2 Instructor view - Modern design."""
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
    return render(request, "v2/pages/instructor.html", context)


def safe_round(num):
    """Helper function to reduce syntax repetitions for null checking rounding.

    Returns — if None is passed because that's what appears on the site when there's no data.
    """
    if num is not None:
        return round(num, 2)
    return "\u2014"


def club_category(request, category_slug: str):
    """View for club category page."""
    mode = parse_mode(request)[0]  # Only use the mode, ignoring is_club

    # Get the category by slug
    category = get_object_or_404(ClubCategory, slug=category_slug.upper())

    # Get clubs in this category
    clubs = Club.objects.filter(category=category).order_by("name")

    # Pagination
    page_number = request.GET.get("page", 1)
    paginator = Paginator(clubs, 10)  # 10 clubs per page
    try:
        paginated_clubs = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_clubs = paginator.page(1)
    except EmptyPage:
        paginated_clubs = paginator.page(paginator.num_pages)

    # Navigation breadcrumbs
    breadcrumbs = [
        ("Clubs", reverse("browse") + "?mode=clubs", False),
        (category.name, None, True),
    ]

    return render(
        request,
        "club/category.html",
        {
            "is_club": True,
            "mode": mode,
            "category": category,
            "paginated_clubs": paginated_clubs,
            "breadcrumbs": breadcrumbs,
        },
    )


def club_category_v2(request, category_slug: str):
    """V2 view for club category page."""
    mode = parse_mode(request)[0]
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
        "v2/pages/club_category.html",
        {
            "is_club": True,
            "mode": mode,
            "category": category,
            "paginated_clubs": paginated_clubs,
            "breadcrumbs": breadcrumbs,
        },
    )


def club_view_v2(request, category_slug: str, club_id: int):
    """V2 view for club detail page."""
    mode = parse_mode(request)[0]
    club = get_object_or_404(Club, id=club_id, category__slug=category_slug.upper())
    return render(
        request,
        "v2/pages/club.html",
        _build_club_page_context(request, club, mode, v2=True),
    )
