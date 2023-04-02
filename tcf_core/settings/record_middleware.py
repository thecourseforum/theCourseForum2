import ast


class RecordMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'previous_paths' and 'previous_paths_titles' in request.COOKIES:
            previous_paths = request.COOKIES['previous_paths']
            # Converts string representation of list into list object
            previous_paths = ast.literal_eval(previous_paths)

            previous_paths_titles = request.COOKIES['previous_paths_titles']
            # Converts string representation of list into list object
            previous_paths_titles = ast.literal_eval(previous_paths_titles)

            # Keeps top 10 items in list
            # Only keeps 9 here since 1 is inserted immediately after
            if len(previous_paths) > 9:
                previous_paths = previous_paths[:9]
                previous_paths_titles = previous_paths_titles[:9]
        else:
            previous_paths = []
            previous_paths_titles = []

        response = self.get_response(request)
        if check_path(request.path) and request.session.get('instructor_fullname') is not None:
            # previous_paths.append(request.build_absolute_uri())
            previous_paths.insert(0, request.build_absolute_uri())
            previous_paths = list(dict.fromkeys(previous_paths))
            response.set_cookie('previous_paths', previous_paths)

            title = request.session.get('course_code') + ' - ' + request.session.get('course_title')
            if request.session.get('instructor_fullname') is not None:
                title += ' - ' + request.session.get('instructor_fullname')

            # previous_paths_titles.append(title)
            previous_paths_titles.insert(0, title)
            previous_paths_titles = list(dict.fromkeys(previous_paths_titles))
            response.set_cookie('previous_paths_titles', previous_paths_titles)
        return response


# checks the first path ("/path/...") for invalid paths.
# returns false on api and browse paths
# only returns true for paths that include "/course/" in some portion of it
def check_path(request_path):
    if "course" not in request_path:
        return False
    if len(request_path) <= 1:
        return True
    path_string = str(request_path)[1:]
    non_course_dep = ["api", "browse"]
    for first_path in non_course_dep:
        if path_string[:path_string.index("/")] == first_path:
            return False
    return True
