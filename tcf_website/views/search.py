# pylint: disable=invalid-name
"""Views for search results"""
import re
import statistics
from typing import Iterable

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import F, FloatField, Q, Value
from django.db.models.functions import Greatest, Round
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from ..models import Club, Course, Instructor, Subdepartment


def parse_mode(request):
    """Parse the mode parameter from the request."""
    mode = request.GET.get("mode", "courses")
    return mode, (mode == "clubs")


def group_by_dept(courses):
    """Groups courses by their department and adds relevant data."""
    grouped_courses = {}
    for course in courses:
        course_dept = course["mnemonic"]
        if course_dept not in grouped_courses:
            subdept = Subdepartment.objects.filter(mnemonic=course_dept).first()
            # should only ever have one returned with that mnemonic
            grouped_courses[course_dept] = {
                "subdept_name": subdept.name,
                "dept_id": subdept.department_id,
                "courses": [],
            }
        grouped_courses[course_dept]["courses"].append(course)

    return grouped_courses


def group_by_club_category(clubs):
    """Groups clubs by their category and adds relevant data."""
    grouped = {}
    for club in clubs:
        slug = club["category_slug"]
        if slug not in grouped:
            grouped[slug] = {
                "category_name": club["category_name"],
                "category_slug": slug,
                "clubs": [],
            }
        grouped[slug]["clubs"].append(club)
    return grouped


def paginate_results(request, items, per_page=15):
    """Helper function to paginate items."""
    page_number = request.GET.get("page", 1)
    paginator = Paginator(items, per_page)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return page_obj, paginator.count


def search(request):
    """Search results view."""

    # Set query
    query = request.GET.get("q", "").strip()
    mode, is_club = parse_mode(request)

    filters = {
        "disciplines": request.GET.getlist("discipline"),
        "subdepartments": request.GET.getlist("subdepartment"),
        "weekdays": (
            request.GET.get("weekdays", "").split("-")
            if request.GET.get("weekdays")
            else []
        ),
        "from_time": request.GET.get("from_time"),
        "to_time": request.GET.get("to_time"),
        "page": request.GET.get("page"),
        "open_sections": request.GET.get("open_sections") == "on",
        "min_gpa": request.GET.get("min_gpa"),
    }

    # Filters are now managed by localStorage in the browser
    # No need to save them to the session anymore

    instructors = []
    courses_first = True

    if is_club:
        # Club mode
        clubs = fetch_clubs(query)
        page_obj, total = paginate_results(request, clubs)
        grouped = group_by_club_category(page_obj)
    else:
        # Course mode
        if query:
            # Search mode
            course_results = fetch_courses(query, filters)
            instructors = fetch_instructors(query)
        else:
            # Filter mode
            course_results = filter_courses(filters)

        page_obj, total = paginate_results(request, course_results)

        # Formulate course data
        courses = [
            {
                "id": course.id,
                "title": course.title,
                "number": course.number,
                "mnemonic": course.mnemonic,
                "description": course.description,
                "max_similarity": course.max_similarity if query else 1.0,
            }
            for course in page_obj
        ]

        # Determine display order - courses or instructors first
        if not request.GET.get("page"):
            courses_first = decide_order(courses, instructors) if query else True

        grouped = group_by_dept(courses)

    ctx = {
        "mode": mode,
        "is_club": is_club,
        "query": query[:30] + ("..." if len(query) > 30 else ""),
        "courses_first": courses_first,
        "grouped": grouped,
        "instructors": instructors,
        "total": total,
        "page_obj": page_obj,
    }

    return render(request, "search/search.html", ctx)


def fetch_clubs(query):
    """Get club data using Django Trigram similarity."""
    threshold = 0.15
    if not query:
        return list(
            Club.objects.annotate(
                max_similarity=Value(1.0, output_field=FloatField()),
                category_slug=F("category__slug"),
                category_name=F("category__name"),
            ).values(
                "id",
                "name",
                "description",
                "max_similarity",
                "category_slug",
                "category_name",
            )
        )

    qs = (
        Club.objects.annotate(sim=TrigramSimilarity("combined_name", query))
        .annotate(max_similarity=F("sim"))
        .filter(max_similarity__gte=threshold)
        .annotate(category_slug=F("category__slug"), category_name=F("category__name"))
        .order_by("-max_similarity")
    )

    return [
        {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "max_similarity": c.max_similarity,
            "category_slug": c.category_slug,
            "category_name": c.category_name,
        }
        for c in qs
    ]


def decide_order(courses: list[dict], instructors: list[dict]) -> bool:
    """Decides if courses (True) or instructors (False) should be displayed first."""

    def mean(scores: Iterable[int]) -> float:
        """Computes and returns the average similarity score."""
        return statistics.mean(_scores) if (_scores := list(scores)) else 0

    courses_avg = mean(course["max_similarity"] for course in courses)
    instructors_avg = mean(instructor["max_similarity"] for instructor in instructors)

    return courses_avg > instructors_avg or not instructors


def fetch_instructors(query) -> list[dict]:
    """Get instructor data using Django Trigram similarity"""
    # arbitrarily chosen threshold
    similarity_threshold = 0.5
    results = (
        Instructor.objects.only("first_name", "last_name", "full_name", "email")
        .annotate(
            similarity_first=TrigramSimilarity("first_name", query),
            similarity_last=TrigramSimilarity("last_name", query),
            similarity_full=TrigramSimilarity("full_name", query),
        )
        .annotate(
            max_similarity=Greatest(
                F("similarity_first"),
                F("similarity_last"),
                F("similarity_full"),
                output_field=FloatField(),
            )
        )
        .filter(Q(max_similarity__gte=similarity_threshold))
        .order_by("-max_similarity")[:10]
    )

    instructors = [
        {
            key: getattr(instructor, key)
            for key in ("first_name", "last_name", "email", "id", "max_similarity")
        }
        for instructor in results
    ]

    return instructors


def fetch_courses(query, filters):
    """Get course data using Django Trigram similarity"""
    # lower similarity threshold for partial searches of course titles
    similarity_threshold = 0.15

    def normalize_search_query(q: str) -> str:
        # if "<mnemonic><number>" pattern present without space, add one to adhere to index pattern
        pattern = re.compile(r"^([A-Za-z]{1,4})(\d{4})$")
        match = pattern.match(q)

        return f"{match.group(1)} {match.group(2)}" if match else q

    search_query = normalize_search_query(query)

    results = (
        Course.objects.select_related("subdepartment")
        .only("title", "number", "subdepartment__mnemonic", "description")
        .annotate(
            mnemonic_similarity=TrigramSimilarity(
                "combined_mnemonic_number", search_query
            ),
            title_similarity=TrigramSimilarity("title", search_query),
        )
        # round results to two decimal places
        .annotate(
            max_similarity=Round(
                Greatest(
                    F("mnemonic_similarity"),
                    F("title_similarity"),
                ),
                2,
            )
        )
        # expose mnemonic to view
        .annotate(mnemonic=F("subdepartment__mnemonic"))
    )

    # Apply filters
    results = apply_filters(results, filters)

    results = (
        results.filter(max_similarity__gte=similarity_threshold)
        .filter(Q(number__isnull=True) | Q(number__regex=r"^\d{4}$"))
        .exclude(semester_last_taught_id__lt=48)
        .order_by("-max_similarity")
    )

    return results


def filter_courses(filters):
    """Get filtered courses without search functionality."""
    results = (
        Course.objects.select_related("subdepartment")
        .only("title", "number", "subdepartment__mnemonic", "description")
        .annotate(mnemonic=F("subdepartment__mnemonic"))
        .filter(Q(number__isnull=True) | Q(number__regex=r"^\d{4}$"))
        .exclude(semester_last_taught_id__lt=48)
    )

    # Apply filters
    results = apply_filters(results, filters)

    results = results.order_by("subdepartment__mnemonic", "number")

    return results


def apply_filters(results, filters):
    """Apply filters to course queryset."""
    if filters.get("disciplines"):
        results = results.filter(disciplines__name__in=filters.get("disciplines"))

    if filters.get("subdepartments"):
        results = results.filter(
            subdepartment__mnemonic__in=filters.get("subdepartments")
        )

    weekdays = [day for day in filters.get("weekdays", []) if day]
    from_time = filters.get("from_time")
    to_time = filters.get("to_time")

    if len(weekdays) != 5 and len(weekdays) != 0 or from_time or to_time:
        time_filtered = Course.filter_by_time(
            days=weekdays, start_time=from_time, end_time=to_time
        )
        results = results.filter(id__in=time_filtered.values_list("id", flat=True))

    if filters.get("open_sections"):
        open_sections_filtered = Course.filter_by_open_sections()
        results = results.filter(
            id__in=open_sections_filtered.values_list("id", flat=True)
        )

    min_gpa = filters.get("min_gpa")
    if min_gpa:
        try:
            min_gpa_float = float(min_gpa)
            # Filter directly using a subquery on CourseGrade
            results = results.filter(coursegrade__average__gte=min_gpa_float)
        except (ValueError, TypeError):
            # Silently ignore invalid values
            pass

    return results.distinct()
