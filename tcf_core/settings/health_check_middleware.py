"""Middleware to handle health check requests without ALLOWED_HOSTS validation."""
from django.http import HttpResponse


class HealthCheckMiddleware:
    """Bypass ALLOWED_HOSTS for health check endpoint."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/health":
            return HttpResponse("ok")
        return self.get_response(request)
