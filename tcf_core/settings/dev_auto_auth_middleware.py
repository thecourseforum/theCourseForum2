"""Dev-only middleware that auto-authenticates a session-specific test user.

Allows local development without Cognito and supports testing multiple
concurrent users across separate browser sessions/incognito windows.
"""

import os
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model, login


class DevAutoAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only in dev environment
        if os.environ.get("ENVIRONMENT") == "dev":
            # If not authenticated, create or fetch a session-specific user and log in
            if not getattr(request, "user", None) or not request.user.is_authenticated:
                # Allow overriding user via query, e.g., ?as=alice
                username = request.GET.get("as")
                if not username:
                    username = request.COOKIES.get("tcf_dev_user")

                if not username:
                    # Ensure a session key exists to derive a stable username per session
                    if not request.session.session_key:
                        request.session.save()
                    session_key = request.session.session_key or secrets.token_hex(8)
                    username = f"devuser-{session_key[:8]}"

                User = get_user_model()
                user, _created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "email": f"{username}@example.test",
                        "is_active": True,
                        # Ensure unique, non-empty computing_id to satisfy DB constraint
                        "computing_id": username[:20],
                        # Optional friendly name
                        "first_name": "Dev",
                        "last_name": username[:20],
                    },
                )

                # Log in with the standard ModelBackend
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")

                # Flag to set a cookie on the response so the username persists in this session
                if not request.COOKIES.get("tcf_dev_user"):
                    setattr(request, "_set_dev_user_cookie", username)

        response = self.get_response(request)

        # Set the dev user cookie if needed
        dev_cookie_username = getattr(request, "_set_dev_user_cookie", None)
        if dev_cookie_username:
            response.set_cookie("tcf_dev_user", dev_cookie_username, httponly=False)

        return response