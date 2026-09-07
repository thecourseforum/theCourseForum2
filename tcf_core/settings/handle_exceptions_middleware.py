"""Middleware for recording errors to print out."""

import json
import sys
import traceback

from django.core.exceptions import PermissionDenied
from django.http import Http404


class HandleExceptionsMiddleware:
    """Logs unexpected exceptions as a single JSON line for ECS/CloudWatch."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        """Log unexpected exceptions; skip expected 404/403 responses."""
        if isinstance(exception, (Http404, PermissionDenied)):
            return None
        print(
            json.dumps(
                {
                    "level": "ERROR",
                    "path": request.get_full_path(),
                    "method": request.method,
                    "ip": request.META.get(
                        "HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR")
                    ),
                    "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                    "exception": type(exception).__name__,
                    "message": str(exception),
                    "traceback": traceback.format_exc(),
                }
            ),
            file=sys.stderr,
        )
        return None
