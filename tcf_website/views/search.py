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

    courses = fetch_courses(query)
    instructors = fetch_instructors(query)
    courses_first = decide_order(courses, instructors)

    ctx = {
        "query": query[:30] + ("..." if len(query) > 30 else ""),
        "courses_first": courses_first,
        "courses": group_by_dept(courses),
        "instructors": instructors,
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
        .order_by("-max_similarity")[:10]
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
