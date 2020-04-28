"""Views for search results"""
import os
import json
import requests

from django.shortcuts import render
#from django.contrib.auth.decorators import login_required


def search(request):
    """Search results view."""

    # Set query
    query = request.GET.get('q', '')

    # Set endpoints
    courses_search_endpoint = os.environ['ES_COURSE_SEARCH_ENDPOINT']
    instructors_search_endpoint = os.environ['ES_INSTRUCTOR_SEARCH_ENDPOINT']

    # Fetch results
    response1 = fetch_elasticsearch(query, courses_search_endpoint)
    response2 = fetch_elasticsearch(query, instructors_search_endpoint)

    # Format results
    courses = format_response(response1)
    instructors = format_response(response2)

    # Arguments for template
    args = {
        "courses": courses,
        "instructors": instructors,
        "query": query
    }

    return render(request, 'search/search.html', args)


def fetch_elasticsearch(query, api_endpoint):
    """Fetches documents based on a query from a Document API endpoint"""

    api_key = os.environ['ES_PUBLIC_API_KEY']
    https_headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key
    }

    # Format API query string
    json_query = build_elasticsearch_query(query, api_endpoint)

    try:
        response = requests.get(
            url=api_endpoint,
            headers=https_headers,
            data=json_query
        )
        return response

    except requests.RequestException as error:
        return "Error: " + str(error)


def format_response(response):
    """Formats an Elastic search endpoint response"""

    body = json.loads(response.text)
    engine = body.get("meta").get("engine").get("name")
    results = body.get("results")

    if engine == "uva-courses":
        return format_courses(results)
    if engine == "uva-instructors":
        return format_instructors(results)

    return "Unknown engine, please verify engine exists"


def format_courses(results):
    """Formats courses engine results"""

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
    """Formats instructors engine results"""

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


def build_elasticsearch_query(query, api_endpoint):
    """Returns an api-specific Elastic query"""

    if api_endpoint == os.environ['ES_COURSE_SEARCH_ENDPOINT']:
        return build_courses_query(query)
    if api_endpoint == os.environ['ES_INSTRUCTOR_SEARCH_ENDPOINT']:
        return build_instructors_query(query)

    return json.dumps({"query": query}) # MOST BASIC QUERY


def build_courses_query(query):
    """Returns the courses search algorithm"""

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


def build_instructors_query(query):
    """Returns the instructors search algorithm"""

    return json.dumps({"query": query}) #still need to design algorithm
