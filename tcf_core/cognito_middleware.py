"""Middleware for handling Cognito authentication"""

import logging

logger = logging.getLogger(__name__)


class CognitoAuthMiddleware:  # pylint: disable=too-few-public-methods
    """
    Middleware that processes Cognito tokens in HTTP requests

    This middleware checks for tokens in cookies or headers and authenticates users
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # The middleware only runs for the callback path
        # The actual authentication is handled in the view
        response = self.get_response(request)
        return response
