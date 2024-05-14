# pylint: disable=invalid-name
"""Views for search results"""

import re
from datetime import datetime

from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramWordSimilarity,
)
from django.db.models import TextField, Value
from django.db.models.functions import Cast, Concat
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page

from ..models import Course, Instructor, Subdepartment


def search(request):
    """Search results view."""

    # Set query
    query: str = request.GET.get("q", "")

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

    # Set arguments for template view
    args = set_arguments(query, courses, instructors, courses_first)
    context_vars = args

    # Load template view
    return render(request, "search/search.html", context_vars)


# TODO: is this useful?
# before, prioritized courses for short queries (len < 4) - is this a valid strat?
def decide_order(query, courses, instructors):
    """Decides if courses or instructors should be displayed first.
    Returns True if courses should be prioritized, False if instructors should be prioritized
    """

    if (
        len(instructors["results"]) == 0
        or instructors["results"][0]["score"] == 0
    ):
        return True

    # Prioritize perfect match for professor names
    if instructors["results"][0]["score"] == 1.0:
        return False

    courses_avg = compute_avg_similarity(
        [x["score"] for x in courses["results"]]
    )

    return courses_avg != 0


def compute_avg_similarity(scores):
    """Computes and returns the average similarity score."""
    return sum(scores) / len(scores) if len(scores) > 0 else 0


def fetch_instructors(query: str):
    """Get instructor data using Django Trigram similarity"""
    results = (
        Instructor.objects.only("first_name", "last_name")
        .annotate(full_name=Concat("first_name", Value(" "), "last_name"))
        .annotate(similarity=TrigramWordSimilarity(query, "full_name"))
        .filter(similarity__gte=0.2)
        .order_by("-similarity")[:10]
    )

    formatted_results = [
        {
            "_meta": {"id": str(instructor.pk), "score": instructor.similarity},
            "first_name": {"raw": instructor.first_name},
            "last_name": {"raw": instructor.last_name},
            "email": {"raw": instructor.email},
            "website": {
                "raw": (
                    instructor.website
                    if hasattr(instructor, "website")
                    else None
                )
            },
        }
        for instructor in results
    ]

    return format_response(
        {
            "results": formatted_results,
            "meta": {"engine": {"name": "tcf-instructors"}},
        }
    )


def fetch_courses(title, number):
    """Get course data using reverse indexing"""
    vector = (
        SearchVector("title", weight='A', config='simple')
        + SearchVector("subdepartment__mnemonic", weight='B', config='simple')
        + SearchVector(Cast("number", TextField()), weight='C', config='simple')
    )
    query_string = f"{title} {number}" if number else title
    query = SearchQuery(query_string, config='simple')

    results = (
        Course.objects.annotate(rank=SearchRank(vector, query))
        .order_by('-rank')
        .exclude(semester_last_taught_id__lt=48)[:10]
    )

    formatted_results = [
        {
            # TODO: normalize score
            "_meta": {"id": str(course.pk), "score": course.rank},
            "title": {"raw": course.title},
            "number": {"raw": course.number},
            "mnemonic": {
                "raw": course.subdepartment.mnemonic + " " + str(course.number)
            },
            "description": {"raw": course.description},
        }
        for course in results
    ]

    return format_response(
        {
            "results": formatted_results,
            "meta": {"engine": {"name": "tcf-courses"}},
        }
    )


def format_response(response):
    """Formats an Trigram response."""
    formatted = {"error": False, "results": []}
    if "error" in response:
        formatted["error"] = True
        return formatted

    engine = response.get("meta").get("engine").get("name")
    results = response.get("results")
    if engine == "tcf-courses":
        formatted["results"] = format_courses(results)
    elif engine == "tcf-instructors":
        formatted["results"] = format_instructors(results)
    else:
        formatted["error"] = True
        formatted["message"] = "Unknown engine, please verify engine exists"

    return formatted


def format_courses(results):
    """Formats courses engine results."""
    formatted = []
    for result in results:
        course = {
            "id": result.get("_meta").get("id"),
            "title": result.get("title").get("raw"),
            "number": result.get("number").get("raw"),
            "mnemonic": result.get("mnemonic").get("raw"),
            "description": result.get("description").get("raw"),
            "score": result.get("_meta").get("score"),
        }
        formatted.append(course)
    return formatted


def format_instructors(results):
    """Formats instructors engine results."""
    formatted = []
    for result in results:
        instructor = {
            "id": result.get("_meta").get("id"),
            "first_name": result.get("first_name").get("raw"),
            "last_name": result.get("last_name").get("raw"),
            "email": result.get("email").get("raw"),
            "website": result.get("website").get("raw"),
            "score": result.get("_meta").get("score"),
        }
        formatted.append(instructor)
    return formatted


def set_arguments(query, courses, instructors, courses_first):
    """Sets the search template arguments."""
    args = {"query": query}
    if not courses["error"]:
        args["courses"] = group_by_dept(courses["results"])
    if not instructors["error"]:
        args["instructors"] = instructors["results"]

    args["courses_first"] = courses_first

    args["displayed_query"] = query[:30] + "..." if len(query) > 30 else query
    return args


def group_by_dept(courses):
    """Groups courses by their department and adds relevant data."""
    grouped_courses = {}
    for course in courses:
        course_dept = course["mnemonic"][: course["mnemonic"].index(" ")]
        if course_dept not in grouped_courses:
            subdept = Subdepartment.objects.filter(mnemonic=course_dept)[0]
            # should only ever have one returned with that mnemonic
            grouped_courses[course_dept] = {
                "subdept_name": subdept.name,
                "dept_id": subdept.department_id,
                "courses": [],
            }
        grouped_courses[course_dept]["courses"].append(course)

    return grouped_courses


# cache autocomplete results for 60s * 5 = 5min
@cache_page(60 * 5)
def autocomplete(request):
    """Fetch autocomplete results"""
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

    # fetching instructor results from query
    instructorData = fetch_instructors(query)["results"]
    # normalizing instructor data
    for instructor in instructorData:
        instructor["score"] = instructor.pop("score") / 2.5
        instructor["title"] = (
            instructor.pop("first_name") + " " + instructor.pop("last_name")
        )

    courses = fetch_courses(title_part, number_part)
    courseData = list(courses["results"])

    combinedData = instructorData + courseData

    # sort the top results using the compare function
    topResults = sorted(combinedData, key=compare, reverse=True)[:5]

    return JsonResponse({"results": topResults})


# pylint: disable=missing-function-docstring
def compare(result):
    similarity_threshold = 0.01

    meetsThreshold = float("-inf")

    try:
        print(f'{result["title"]} has score {result["score"]}')
        if result["score"] > similarity_threshold:
            meetsThreshold = result["score"]
    except Exception as _:  # pylint: disable=broad-exception-caught
        if result["total_similarity"] > similarity_threshold:
            meetsThreshold = result["total_similarity"]
    return meetsThreshold
