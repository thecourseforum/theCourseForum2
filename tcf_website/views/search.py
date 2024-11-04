# pylint: disable=invalid-name
"""Views for search results"""
import re

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import F, FloatField, Q
from django.db.models.functions import Greatest
from django.shortcuts import render

from ..models import Course, Instructor, Subdepartment


def search(request):
    """Search results view."""

    # Set query
    query = request.GET.get("q", "")

    courses = fetch_courses(query)
    instructors = fetch_instructors(query)

    courses_first = decide_order(query, courses, instructors)

    # Set arguments for template view
    args = set_arguments(query, courses, instructors, courses_first)
    context_vars = args

    # Load template view
    return render(request, "search/search.html", context_vars)


def decide_order(query, courses, instructors):
    """Decides if courses or instructors should be displayed first.
    Returns True if courses should be prioritized, False if instructors should be prioritized
    """

    # Calculate average similarity for courses
    courses_avg = compute_avg_similarity([x["score"] for x in courses["results"]])

    # Calculate average similarity for instructors
    instructors_avg = compute_avg_similarity([x["score"] for x in instructors["results"]])

    # Define a threshold for the minimum average similarity score. This value can be adjusted.
    THRESHOLD = 0.5

    # Scores of the closest match for both
    first_instructor_score = 0
    first_course_score = 0
    if len(instructors["results"]) > 0:
        first_instructor_score = instructors["results"][0]["score"]
    if len(courses["results"]) > 0:
        first_course_score = courses["results"][0]["score"]

    # If there is a perfect match for any part of the professor's name, return that
    # unless it also perfectly matches a course
    if first_instructor_score == 1.0 and first_instructor_score >= first_course_score:
        return False

    # Prioritize courses for short queries or if their average similarity
    # score is significantly higher
    if len(query) <= 4 or (courses_avg > instructors_avg and courses_avg > THRESHOLD):
        return True

    # Prioritize courses if professor search result length is 0, regardless of course results
    if len(instructors["results"]) <= 0:
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
    formatted_results = [
        {
            "_meta": {
                "id": str(instructor.pk),
                "score": instructor.similarity_max,
            },
            "first_name": {"raw": instructor.first_name},
            "last_name": {"raw": instructor.last_name},
            "email": {"raw": instructor.email},
            "website": {"raw": (instructor.website if hasattr(instructor, "website") else None)},
        }
        for instructor in results
    ]

    return format_response(
        {
            "results": formatted_results,
            "meta": {"engine": {"name": "tcf-instructors"}},
        }
    )


def fetch_courses(query):
    """Get course data using Django Trigram similarity"""
    # lower similarity threshold for partial searches of course titles
    similarity_threshold = 0.25

    def normalize_search_query(q: str) -> str:
        # if "<mnemonic><number>" pattern present without a space, add one to adhere to index pattern
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
        .annotate(
            max_similarity=Greatest(
                F("mnemonic_similarity"),
                F("title_similarity"),
            )
        )
        .filter(max_similarity__gte=similarity_threshold)
        # filters out classes with 3 digit class numbers (old naming system)
        .filter(Q(number__isnull=True) | Q(number__regex=r"^\d{4}$"))
        # filters out classes that haven't been taught since Fall 2020
        .exclude(semester_last_taught_id__lt=48)
        .order_by("-max_similarity")[:10]
    )

    formatted_results = [
        {
            "_meta": {"id": str(course.pk), "score": course.max_similarity},
            "title": {"raw": course.title},
            "number": {"raw": course.number},
            "mnemonic": {"raw": course.subdepartment.mnemonic + " " + str(course.number)},
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
