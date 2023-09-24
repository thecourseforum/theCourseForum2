"""Views for search results"""

import re
import statistics

from django.contrib.postgres.search import TrigramWordSimilarity
from django.db.models import CharField, ExpressionWrapper, F, FloatField, Value
from django.db.models.functions import Cast, Concat
from django.shortcuts import render

from ..models import Course, Instructor, Subdepartment


def search(request):
    """Search results view."""

    # Set query
    query = request.GET.get("q", "")
    match = re.match(r"([a-zA-Z]{2,})\s*(\d*)", query)
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


def compute_zscore(scores):
    """Computes and returns the z_score from the list
    and gets the z-score of the highest z-score."""
    if len(scores) > 1:
        mean = statistics.mean(scores)

        stddev = statistics.stdev(scores, mean)
        if stddev == 0:
            stddev = 1
        z_score = scores[0] - mean
        z_score /= stddev

        return z_score
    # Returns 0 for only one item (can't compute z-score) or -1 if no items
    if len(scores) == 1:
        return 0

    return -1


def decide_order(query, courses, instructors):
    """Decides if courses or instructors should be displayed first.
    Returns True if courses should be prioritized, False if instructors should be prioritized
    """

    # Calculate average similarity for courses
    courses_avg = compute_avg_similarity([x["score"] for x in courses["results"]])

    # Calculate average similarity for instructors
    instructors_avg = compute_avg_similarity(
        [x["score"] for x in instructors["results"]]
    )

    # Define a threshold for the minimum average similarity score. This value can be adjusted.
    THRESHOLD = 0.5

    # Prioritize courses for short queries or if their average similarity score is significantly higher
    if len(query) <= 4 or (courses_avg > instructors_avg and courses_avg > THRESHOLD):
        return True

    return False


def compute_avg_similarity(scores):
    """Computes and returns the average similarity score."""
    length = 0
    total = 0
    for score in scores:
        total += score
        length += 1
    return 0 if length == 0 else total / length


def fetch_instructors(query):
    """Get instructor data using Django Trigram similarity"""
    results = (
        Instructor.objects.only("first_name", "last_name")
        .annotate(full_name=Concat("first_name", Value(" "), "last_name"))
        .annotate(similarity=TrigramWordSimilarity(query, "full_name"))
        .filter(similarity__gte=0.2)
        .order_by("-similarity")[:20]
    )
    # Formatting results similar to Elastic search response
    formatted_results = [
        {
            "_meta": {"id": str(instructor.pk), "score": instructor.similarity},
            "first_name": {"raw": instructor.first_name},
            "last_name": {"raw": instructor.last_name},
            "email": {"raw": instructor.email},
            "website": {
                "raw": instructor.website if hasattr(instructor, "website") else None
            },
        }
        for instructor in results
    ]

    return format_response(
        {"results": formatted_results, "meta": {"engine": {"name": "tcf-instructors"}}}
    )


def fetch_courses(title, number):
    """Get course data using Django Trigram similarity"""
    MNEMONIC_WEIGHT = 1.5
    NUMBER_WEIGHT = 1
    TITLE_WEIGHT = 1
    if number != "":
        TITLE_WEIGHT = 0
    else:
        NUMBER_WEIGHT = 0
    results = (
        Course.objects.select_related("subdepartment")
        .only("title", "number", "subdepartment__mnemonic", "description")
        .annotate(
            mnemonic_similarity=TrigramWordSimilarity(title, "subdepartment__mnemonic"),
            number_similarity=TrigramWordSimilarity(
                number, Cast("number", CharField())
            ),
            title_similarity=TrigramWordSimilarity(title, Cast("title", CharField())),
        )
        .annotate(
            total_similarity=ExpressionWrapper(
                F("mnemonic_similarity") * MNEMONIC_WEIGHT
                + F("number_similarity") * NUMBER_WEIGHT
                + F("title_similarity") * TITLE_WEIGHT,
                output_field=FloatField(),
            )
        )
        .filter(total_similarity__gte=0.2)
        .order_by("-total_similarity")[:20]
    )

    # Formatting results similar to Elastic search response
    formatted_results = [
        {
            "_meta": {"id": str(course.pk), "score": course.total_similarity},
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
        {"results": formatted_results, "meta": {"engine": {"name": "tcf-courses"}}}
    )


def format_response(response):
    """Formats an Elastic search endpoint response."""
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
