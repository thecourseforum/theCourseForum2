"""Middleware for recording errors to print out."""

import sys
import traceback


# Source: https://gist.github.com/defrex/6140951
def pretty_request(request):
    """Prints request details and headers."""
    headers = ''
    for header, value in request.META.items():
        if not header.startswith('HTTP'):
            continue
        header = '-'.join([h.capitalize() for h in header[5:].lower().split('_')])
        headers += f'{header}: {value}\n'

    return (
        f'{request.method} HTTP/1.1\n'
        f'Content-Length: {request.META.get("CONTENT_LENGTH", "Unknown")}\n'
        f'Content-Type: {request.META.get("CONTENT_TYPE", "Unknown")}\n'
        f'{headers}\n\n'
        f'{request.body}'
    )


class HandleExceptionsMiddleware:
    """Records information about errors at any point."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        return response

    def process_exception(self, request, exception): # pylint: disable=unused-argument
        """Gets and prints out all errors to terminal for tracking"""
        print("========= Internal server error =========", file=sys.stderr)
        print("========== Request path ==========", file=sys.stderr)
        print(request.get_full_path(), file=sys.stderr)
        print("========== Request details ==========", file=sys.stderr)
        print("Request: " + pretty_request(request), file=sys.stderr)
        print("========== Exception ==========", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        print("========================================", file=sys.stderr)
