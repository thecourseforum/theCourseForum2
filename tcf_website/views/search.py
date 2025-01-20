# pylint: disable=invalid-name
"""Views for search results"""
import re
import statistics
from typing import Iterable

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import F, FloatField, Q
from django.db.models.functions import Greatest, Round
from django.shortcuts import render

from ..models import Course, Instructor, Subdepartment


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


def search(request):
    """Search results view."""

    # Set query
    query = request.GET.get("q", "")

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

    if query:
        courses = fetch_courses(query)
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


def fetch_courses(query):
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
            mnemonic_similarity=TrigramSimilarity("combined_mnemonic_number", search_query),
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
        .filter(max_similarity__gte=similarity_threshold)
        # filters out classes with 3 digit class numbers (old naming system)
        .filter(Q(number__isnull=True) | Q(number__regex=r"^\d{4}$"))
        # filters out classes that haven't been taught since Fall 2020
        .exclude(semester_last_taught_id__lt=48)
        .order_by("-max_similarity")
    )

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
    if filters.get("disciplines"):
        results = results.filter(disciplines__name__in=filters.get("disciplines"))

    if filters.get("subdepartments"):
        results = results.filter(subdepartment__mnemonic__in=filters.get("subdepartments"))

    if filters.get("instructors"):
        results = results.filter(section__instructors__id__in=filters.get("instructors"))

    # Apply time filters
    weekdays = [day for day in filters.get("weekdays", []) if day]
    from_time = filters.get("from_time")
    to_time = filters.get("to_time")

    print("DEBUG TIME FILTERS")
    print(weekdays, from_time, to_time)
    if any([weekdays, from_time, to_time]):
        time_filtered = Course.filter_by_time(days=weekdays, start_time=from_time, end_time=to_time)
        results = results.filter(id__in=time_filtered.values_list("id", flat=True))
        print(results)
        print("DEBUG TIME FILTERED")

    results = results.distinct().order_by("subdepartment__mnemonic", "number")

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
