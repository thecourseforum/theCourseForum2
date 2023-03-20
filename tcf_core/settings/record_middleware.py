import ast


class RecordMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        query = request.GET.get('q', '')

        if 'previous_paths' and 'previous_paths_titles' in request.COOKIES:
            previous_paths = request.COOKIES['previous_paths']
            # Converts string representation of list into list object
            previous_paths = ast.literal_eval(previous_paths)

            previous_paths_titles = request.COOKIES['previous_paths_titles']
            # Converts string representation of list into list object
            previous_paths_titles = ast.literal_eval(previous_paths_titles)

            if len(previous_paths) > 10:
                previous_paths = previous_paths[len(previous_paths) - 10:]
                previous_paths_titles = previous_paths_titles[len(previous_paths_titles) - 10:]
        else:
            previous_paths = []
            previous_paths_titles = []
        if 'count' in request.COOKIES:
            count = int(request.COOKIES['count'])
        else:
            count = 0

        response = self.get_response(request)
        if check_path(request.path):
            previous_paths = [*set(previous_paths)]
            previous_paths_titles = [*set(previous_paths_titles)]

            response.set_cookie('count', count + 1)
            previous_paths.append(request.build_absolute_uri())
            response.set_cookie('previous_paths', previous_paths)

            title = request.session.get('course_code')
            if request.session.get('instructor_fullname') is not None:
                title += ' - ' + request.session.get('instructor_fullname')
            title += ' - theCourseForum'
            previous_paths_titles.append(title)
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
