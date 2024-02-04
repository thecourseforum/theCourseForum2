"""Inject extra context to TCF templates."""

import ast

from django.conf import settings

from tcf_website.models import Semester


def base(request):
    """Inject user + latest semester info."""
    return {
        "DEBUG": settings.DEBUG,
        "USER": request.user,
        "LATEST_SEMESTER": Semester.latest(),
    }


def history_cookies(request):
    """Puts history from cookies into context variables."""
    if "previous_paths" in request.COOKIES:
        previous_paths = request.COOKIES["previous_paths"]
        previous_paths = ast.literal_eval(previous_paths)
    else:
        previous_paths = ""

    if "previous_paths_titles" in request.COOKIES:
        previous_paths_titles = request.COOKIES["previous_paths_titles"]
        previous_paths_titles = ast.literal_eval(previous_paths_titles)
    else:
        previous_paths_titles = ""

    previous_paths_titles = [
        title[:80] + "..." for title in previous_paths_titles
    ]

    previous_paths_and_titles = None
    if len(previous_paths) > 0 and len(previous_paths_titles) > 0:
        previous_paths_and_titles = zip(previous_paths, previous_paths_titles)

    return {
        "previous_paths": previous_paths,
        "previous_path_titles": previous_paths_titles,
        "previous_paths_and_titles": previous_paths_and_titles,
    }
