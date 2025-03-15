# pylint: disable=invalid-name
"""Views for search results"""
import re
import statistics
from typing import Iterable

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import F, FloatField, Q
from django.db.models.functions import Greatest, Round
from django.shortcuts import render
from django.core.cache import cache
from django.views.decorators.cache import cache_page

from ..models import Course, Instructor, Subdepartment


def group_by_dept(courses):
    """Groups courses by their department and adds relevant data."""
    # Get all unique mnemonics from courses
    mnemonics = set(course["mnemonic"] for course in courses)

    # Fetch all subdepartments in a single query
    subdepts = {
        subdept.mnemonic: subdept
        for subdept in Subdepartment.objects.filter(mnemonic__in=mnemonics)
    }

    grouped_courses = {}
    for course in courses:
        course_dept = course["mnemonic"]

        # Skip courses without valid subdepartment
        if course_dept not in subdepts:
            continue

        subdept = subdepts[course_dept]

        if course_dept not in grouped_courses:
            grouped_courses[course_dept] = {
                "subdept_name": subdept.name,
                "dept_id": subdept.department_id,
                "courses": [],
            }

        grouped_courses[course_dept]["courses"].append(course)

    return grouped_courses


@cache_page(60 * 15)  # Cache for 15 minutes
def search(request):
    """Search results view."""

    # Set query
    query = request.GET.get("q", "").strip()

    filters = {
        "disciplines": request.GET.getlist("discipline"),
        "subdepartments": request.GET.getlist("subdepartment"),
        "instructors": request.GET.getlist("instructor"),
        "weekdays": (
            request.GET.get("weekdays", "").split("-") if request.GET.get("weekdays") else []
        ),
        "from_time": request.GET.get("from_time"),
        "to_time": request.GET.get("to_time"),
    }

    # Save filters to session
    request.session["search_filters"] = filters

    if query:
        courses = fetch_courses(query, filters)
        instructors = fetch_instructors(query)
        courses_first = decide_order(courses, instructors)
    else:
        courses = filter_courses(filters)
        instructors = []
        courses_first = True

    ctx = {
        "query": query[:30] + ("..." if len(query) > 30 else ""),
        "courses_first": courses_first,
        "courses": group_by_dept(courses),
        "instructors": instructors,
        "total_courses": len(courses),
    }

    return render(request, "search/search.html", ctx)


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
            mnemonic=F("subdepartment__mnemonic"),
            max_similarity=Round(
                Greatest(
                    TrigramSimilarity("combined_mnemonic_number", search_query),
                    TrigramSimilarity("title", search_query),
                ),
                2,
            ),
        )
    )

    # Apply filters
    results = apply_filters(results, filters)

    results = (
        results.filter(max_similarity__gte=similarity_threshold)
        .filter(Q(number__isnull=True) | Q(number__regex=r"^\d{4}$"))
        .exclude(semester_last_taught_id__lt=48)
        .order_by("-max_similarity")
    )[:15]

    courses = [
        {
            key: getattr(course, key)
            for key in (
                "id",
                "title",
                "number",
                "mnemonic",
                "description",
                "max_similarity",
            )
        }
        for course in results
    ]

    return courses


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

    results = results.distinct().order_by("subdepartment__mnemonic", "number")[:15]

    # Convert to same format as fetch_courses
    courses = [
        {
            "id": course.id,
            "title": course.title,
            "number": course.number,
            "mnemonic": course.mnemonic,
            "description": course.description,
            "max_similarity": 1.0,  # default value since we're not searching
        }
        for course in results
    ]

    return courses


def apply_filters(results, filters):
    """Apply filters to course queryset using Q objects for more readable code."""
    filter_conditions = Q()

    if filters.get("disciplines"):
        filter_conditions &= Q(disciplines__name__in=filters.get("disciplines"))

    if filters.get("subdepartments"):
        filter_conditions &= Q(subdepartment__mnemonic__in=filters.get("subdepartments"))

    if filters.get("instructors"):
        filter_conditions &= Q(section__instructors__id__in=filters.get("instructors"))

    if filter_conditions:
        results = results.filter(filter_conditions)

    # Handle time filters
    weekdays = [day for day in filters.get("weekdays", []) if day]
    from_time = filters.get("from_time")
    to_time = filters.get("to_time")

    if (len(weekdays) != 5 and len(weekdays) != 0) or from_time or to_time:
        time_filtered = Course.filter_by_time(days=weekdays, start_time=from_time, end_time=to_time)
        results = results.filter(id__in=time_filtered.values_list("id", flat=True))

    return results
