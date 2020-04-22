"""Views for search results"""
import os
import json
import requests

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def search(request):
    """Search results view."""

    # Set query
    query = request.GET.get('q', '')

    # Set endpoints
    courses_search_endpoint = os.environ['ES_COURSE_SEARCH_ENDPOINT']
    instructors_search_endpoint = os.environ['ES_INSTRUCTOR_SEARCH_ENDPOINT']

    # Fetch results
    courses = fetch(query, courses_search_endpoint)
    instructors = fetch(query, instructors_search_endpoint)

    # Arguments for template
    args = {
        "courses" : courses,
        "instructors" : instructors,
        "query" : query
    }

    return render(request, 'search/search.html', args)


def fetch(query, api_endpoint):
    """Fetches documents based on a query from a Document API endpoint"""

    api_key = os.environ['ES_PUBLIC_API_KEY']
    https_headers = {
        "Content-Type" : "application/json",
        "Authorization" : "Bearer " + api_key
    }

    # Format API query string
    json_query = json.dumps({"query": query})

    try:
        response = requests.get(
            url=api_endpoint,
            headers=https_headers,
            data=json_query
        )
        return response.text

    except Exception as error:
        return "Error: " + str(error)
