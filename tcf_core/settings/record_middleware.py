class RecordMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'previous_path' in request.COOKIES:
            print('previous_path:', request.COOKIES['previous_path'])
        if 'count' in request.COOKIES:
            count = int(request.COOKIES['count'])
            print('count:', count)
        else:
            count = 0

        response = self.get_response(request)
        if check_Path(request.path):
            response.set_cookie('count', count + 1)
            response.set_cookie('previous_path', request.path)
        print("middleware print")
        return response

# checks the first path ("/path/...") for invalid paths.
# returns false on api and browse paths
def check_Path(request_path):
    path_string = str(request_path)[1:]
    non_course_dep = ["api", "browse"]
    for first_path in non_course_dep:
        if path_string[:path_string.index("/")] == first_path:
            return False
    return True
