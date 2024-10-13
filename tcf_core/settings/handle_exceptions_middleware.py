"""Middleware for recording errors to print out."""

import sys
import traceback


# Source: https://gist.github.com/defrex/6140951
def pretty_request(request):
    headers = ''
    for header, value in request.META.items():
        if not header.startswith('HTTP'):
            continue
        header = '-'.join([h.capitalize() for h in header[5:].lower().split('_')])
        headers += '{}: {}\n'.format(header, value)

    return (
        '{method} HTTP/1.1\n'
        'Content-Length: {content_length}\n'
        'Content-Type: {content_type}\n'
        '{headers}\n\n'
        '{body}'
    ).format(
        method=request.method,
        content_length=request.META['CONTENT_LENGTH'],
        content_type=request.META['CONTENT_TYPE'],
        headers=headers,
        body=request.body,
    )


class HandleExceptionsMiddleware:
    """Records information about errors at any point."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        return response

    def process_exception(self, request, exception):
        """Gets and prints out all errors to terminal for tracking"""
        print("========= Internal server error =========", file=sys.stderr)
        print("========== Request path ==========", file=sys.stderr)
        print(request.get_full_path(), file=sys.stderr)
        print("========== Request details ==========", file=sys.stderr)
        print("Request: " + pretty_request(request), file=sys.stderr)
        print("========== Exception ==========", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        print("========================================", file=sys.stderr)
