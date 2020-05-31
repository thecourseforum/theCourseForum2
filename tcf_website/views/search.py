"""Views for search results"""
import os
import json
import requests

from django.shortcuts import render


def search(request):
    """Search results view."""

    # Set query
    query = request.GET.get('q', '')

    # Fetch Elasticsearch data
    courses = fetch_courses(query)
    instructors = fetch_instructors(query)

    courses_first = decide_order(courses, instructors)

    # Set arguments for template view
    args = set_arguments(query, courses, instructors, courses_first)

    # Load template view
    return render(request, 'search/search.html', args)


def fetch_courses(query):
    """Gets Elasticsearch course data."""
    api_endpoint = os.environ['ES_COURSE_SEARCH_ENDPOINT']
    algorithm = rank_course(query)
    response = fetch_elasticsearch(api_endpoint, algorithm)
    return format_response(response)


def fetch_instructors(query):
    """Gets Elasticsearch instructor data."""
    api_endpoint = os.environ['ES_INSTRUCTOR_SEARCH_ENDPOINT']
    algorithm = rank_instructor(query)
    response = fetch_elasticsearch(api_endpoint, algorithm)
    return format_response(response)


def fetch_elasticsearch(api_endpoint, algorithm):
    """Requests a Document API using a specific search algorithm."""
    api_key = os.environ['ES_PUBLIC_API_KEY']
    https_headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key
    }
    try:
        response = requests.get(
            url=api_endpoint,
            headers=https_headers,
            data=algorithm
        )
        if response.status_code != 200:
            response = {
                "error": True,
                "message": "GET request failed w/ status code " +
                           str(response.status_code)
            }
        return response
    except requests.RequestException as error:
        response = {
            "error": True,
            "message": "GET request failed w/ error " + str(error)
        }
        return response


def rank_instructor(query):
    """Returns the instructors search algorithm."""
    algorithm = {
        "query": query,
    }
    return json.dumps(algorithm)  # improve algorithm later


def rank_course(query):
    """Returns the courses search algorithm."""
    algorithm = {
        "query": query,
        "page": {
            "current": 1,
            "size": 15
        },
        "search_fields": {
            "mnemonic": {
                "weight": 10
            },
            "title": {
                "weight": 8
            },
            "description": {
                "weight": 5
            }
        },
        "boosts": {
            "review_count": {
                "type": "functional",
                "function": "logarithmic",
                "operation": "multiply",
                "factor": 2
            }
        }
    }
    return json.dumps(algorithm)


def format_response(response):
    """Formats an Elastic search endpoint response."""
    formatted = {
        "error": False,
        "results": [],
        "highest_score": 0
    }
    if "error" in response:
        formatted["error"] = True
        return formatted

    body = json.loads(response.text)
    engine = body.get("meta").get("engine").get("name")
    print(json.dumps(body, indent=1))
    results = body.get("results")
    if engine == "uva-courses":
        formatted["results"] = format_courses(results)
    elif engine == "uva-instructors":
        formatted["results"] = format_instructors(results)
    else:
        formatted["error"] = True
        formatted["message"] = "Unknown engine, please verify engine exists"

    if results:  # if results is not empty, 1st element will have highest score
        formatted["highest_score"] = results[0].get("_meta").get("score")

    return formatted


def format_courses(results):
    """Formats courses engine results."""
    formatted = []
    for result in results:
        course = {
            "id": result.get("_meta").get("id"),
            "title": result.get("title").get("raw"),
            "description": result.get("description").get("raw"),
            "number": result.get("number").get("raw"),
            "mnemonic": result.get("mnemonic").get("raw")
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
            "website": result.get("website").get("raw")
        }
        formatted.append(instructor)
    return formatted


def set_arguments(query, courses, instructors, courses_first):
    """Sets the search template arguments."""
    args = {
        "query": query,
        "courses_first": courses_first
    }
    if not courses["error"]:
        args["courses"] = courses["results"]
    if not instructors["error"]:
        args["instructors"] = instructors["results"]
    return args


def decide_order(courses, instructors):
    """Determines whether courses or instructors should be displayed first in search page."""
    return courses["highest_score"] > instructors["highest_score"]
