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
    response1 = fetch_courses(query)
    response2 = fetch_instructors(query)

    # Format Elasticsearch data
    courses = format_response(response1)
    instructors = format_response(response2)

    # Set arguments for template view
    args = {
        "courses": courses,
        "instructors": instructors,
        "query": query
    }

    # Load template view
    return render(request, 'search/search.html', args)


def fetch_courses(query):
    """Gets Elasticsearch course data."""
    api_endpoint = os.environ['ES_COURSE_SEARCH_ENDPOINT']
    algorithm = rank_course(query)
    return fetch_elasticsearch(api_endpoint, algorithm)


def fetch_instructors(query):
    """Gets Elasticsearch instructor data."""
    api_endpoint = os.environ['ES_INSTRUCTOR_SEARCH_ENDPOINT']
    algorithm = rank_instructor(query)
    return fetch_elasticsearch(api_endpoint, algorithm)


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
        return response
    except requests.RequestException as error:
        return "Error: " + str(error)


def rank_instructor(query):
    """Returns the instructors search algorithm."""
    algorithm = {
        "query": query
    }
    return json.dumps(algorithm) # improve algorithm later


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
    body = json.loads(response.text)
    engine = body.get("meta").get("engine").get("name")
    results = body.get("results")

    if engine == "uva-courses":
        return format_courses(results)
    if engine == "uva-instructors":
        return format_instructors(results)
    return "Unknown engine, please verify engine exists"


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
