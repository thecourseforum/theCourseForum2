import logging
import uuid
from contextvars import ContextVar

# Thread-safe context variable for request data
request_context: ContextVar[dict] = ContextVar('request_context', default=None)


class RequestLoggingMiddleware:
    """
    Middleware that generates/extracts request IDs and stores request context
    for automatic inclusion in all logs.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate or extract request ID
        request_id = request.headers.get('X-Request-ID')
        if not request_id:
            request_id = str(uuid.uuid4())

        # Store request ID on request object for easy access
        request.request_id = request_id

        # Build initial request context
        context = {
            'request_id': request_id,
            'path': request.path,
            'method': request.method,
        }

        # Add user_id if authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            context['user_id'] = str(request.user.id)

        # Set context for this request
        request_context.set(context)

        # Process request
        response = self.get_response(request)

        # Add status code to context after response
        context['status_code'] = response.status_code

        # Return request ID in response headers for client reference
        response['X-Request-ID'] = request_id

        return response

    def process_exception(self, request, exception):
        """Log exceptions with request context."""
        logger = logging.getLogger('django.request')
        logger.exception(
            f"Exception processing request: {exception}",
            extra={'exception_during_request': True}
        )


class RequestLoggingFilter(logging.Filter):
    """
    Logging filter that injects request context into all log records.
    """

    def filter(self, record):
        # Get current request context
        context = request_context.get()

        if context:
            # Inject all context fields into the log record
            for key, value in context.items():
                setattr(record, key, value)

        return True
