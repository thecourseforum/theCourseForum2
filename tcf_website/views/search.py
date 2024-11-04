# pylint: disable=invalid-name
"""Views for search results"""

import re
import statistics
from typing import Iterable

from django.contrib.postgres.search import TrigramSimilarity, TrigramWordSimilarity
from django.db.models import CharField, ExpressionWrapper, F, FloatField, Q
from django.db.models.functions import Cast, Greatest
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

    # courses are at least 3 digits long
    # https://registrar.virginia.edu/faculty-staff/course-numbering-scheme
    match = re.match(r"([a-zA-Z]{2,})\s*(\d{3,})", query)
    if match:
        title_part, number_part = match.groups()
    else:
        # Handle cases where the query doesn't match the expected format
        title_part, number_part = query, ""

    instructors = fetch_instructors(query)
    courses = fetch_courses(title_part, number_part)
    courses_first = decide_order(query, courses, instructors)

    ctx = {
        "query": query[:30] + ("..." if len(query) > 30 else ""),
        "courses_first": courses_first,
        "courses": group_by_dept(courses),
        "instructors": instructors,
    }

    return render(request, "search/search.html", ctx)


def decide_order(query, courses: list[dict], instructors: list[dict]) -> bool:
    """Decides if courses (True) or instructors (False) should be displayed first."""

    def mean(scores: Iterable[int]) -> float:
        """Computes and returns the average similarity score."""
        return statistics.mean(_scores) if (_scores := list(scores)) else 0

    THRESHOLD = 0.5

    courses_avg = mean(x["similarity_max"] for x in courses)
    instructors_avg = mean(x["similarity_max"] for x in instructors)

    if len(query) <= 4 or (courses_avg > instructors_avg and courses_avg > THRESHOLD):
        return True

    return not instructors


def fetch_instructors(query) -> list[dict]:
    """Get instructor data using Django Trigram similarity"""
    similarity_threshold = 0.5
    results = (
        Instructor.objects.only("first_name", "last_name", "full_name", "email")
        .annotate(
            similarity_first=TrigramSimilarity("first_name", query),
            similarity_last=TrigramSimilarity("last_name", query),
            similarity_full=TrigramSimilarity("full_name", query),
        )
        .annotate(
            similarity_max=Greatest(
                F("similarity_first"),
                F("similarity_last"),
                F("similarity_full"),
                output_field=FloatField(),
            )
        )
        .filter(Q(similarity_max__gte=similarity_threshold))
        .order_by("-similarity_max")[:10]
    )

    instructors = [
        {
            key: getattr(instructor, key)
            for key in ("first_name", "last_name", "email", "id", "similarity_max")
        }
        for instructor in results
    ]

    return instructors


def fetch_courses(title, number) -> list[dict]:
    """Get course data using Django Trigram similarity"""
    MNEMONIC_WEIGHT = 1.5
    NUMBER_WEIGHT = 1
    TITLE_WEIGHT = 1

    # search query of form "<MNEMONIC><NUMBER>"
    if number != "":
        TITLE_WEIGHT = 0
        MNEMONIC_WEIGHT = 1
    # otherwise, "title" is entire query
    else:
        NUMBER_WEIGHT = 0

    results = (
        Course.objects.select_related("subdepartment")
        .only("title", "number", "subdepartment__mnemonic", "description")
        .annotate(
            mnemonic=F("subdepartment__mnemonic"),
            mnemonic_similarity=TrigramWordSimilarity(title, "subdepartment__mnemonic"),
            number_similarity=TrigramWordSimilarity(number, Cast("number", CharField())),
            title_similarity=TrigramWordSimilarity(title, Cast("title", CharField())),
        )
        .annotate(
            similarity_max=ExpressionWrapper(
                F("mnemonic_similarity") * MNEMONIC_WEIGHT
                + F("number_similarity") * NUMBER_WEIGHT
                + F("title_similarity") * TITLE_WEIGHT,
                output_field=FloatField(),
            )
        )
        .filter(similarity_max__gte=0.2)
        # filters out classes with 3 digit class numbers (old naming system)
        .filter(Q(number__isnull=True) | Q(number__regex=r"^\d{4}$"))
        # filters out classes that haven't been taught since Fall 2020
        .exclude(semester_last_taught_id__lt=48)
        .order_by("-similarity_max")[:10]
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
                "similarity_max",
            )
        }
        for course in results
    ]

    return courses
