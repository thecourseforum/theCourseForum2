"""Middleware for recording cookie information."""


class RecordMiddleware:  # pylint: disable=too-few-public-methods
    """
    Previously recorded course section info into cookies.
    Now does nothing as this functionality has been moved to client-side
    localStorage to avoid polluting Django sessions.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request and get response
        response = self.get_response(request)

        # We no longer set cookies for history tracking
        # All history is now managed via localStorage in the browser

        return response


# checks the first path ("/path/...") for invalid paths.
# returns false on api and browse paths
# only returns true for paths that include "/course/" in some portion of it
def check_path(request_path):
    """Checks the first path ("/path/...") for invalid paths."""
    if "course" not in request_path:
        return False
    if len(request_path) <= 1:
        return True
    path_string = str(request_path)[1:]
    non_course_dep = ["api", "browse"]
    for first_path in non_course_dep:
        if path_string[: path_string.index("/")] == first_path:
            return False
    return True
