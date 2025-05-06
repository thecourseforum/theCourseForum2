"""Middleware for recording cookie information."""

import ast


class RecordMiddleware:  # pylint: disable=too-few-public-methods
    """Records information about course section info into cookies."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if "previous_paths_titles" in request.COOKIES:
            previous_paths = request.COOKIES["previous_paths"]
            # Converts string representation of list into list object
            previous_paths = ast.literal_eval(previous_paths)

            previous_paths_titles = request.COOKIES["previous_paths_titles"]
            # Converts string representation of list into list object
            previous_paths_titles = ast.literal_eval(previous_paths_titles)
        else:
            previous_paths = []
            previous_paths_titles = []

        # Process the request and get response
        response = self.get_response(request)

        # We no longer manage history through the middleware
        # This is now handled by client-side JavaScript using localStorage
        # The cookie is still retained for backwards compatibility
        # but it's populated by JavaScript, not by the middleware

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
