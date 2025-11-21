"""Dev-only middleware that auto-logs in a random active user.

This is intended for local development convenience only. It will:
- Run only when ENVIRONMENT == 'dev'
- Skip admin, login/logout, API, static/media paths
- If the request is unauthenticated, log in a random active, non-staff user
"""

import logging
import random

from django.conf import settings
from django.contrib.auth import get_user_model, login

logger = logging.getLogger(__name__)


class DevAutoLoginMiddleware:  # pylint: disable=too-few-public-methods
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # Only act in dev environment
            if str(getattr(settings, "ENVIRONMENT", "")).lower() == "dev":
                path = request.path or ""
                if (
                    not getattr(request, "user", None) or not request.user.is_authenticated
                ) and self._allowed_path(path):
                    user = self._get_or_create_dev_user(request)
                    if user is not None:
                        # Ensure ModelBackend is available for session auth
                        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                        logger.debug("Dev auto-login: logged in as %s", user.username)
        except Exception:  # pragma: no cover
            # Avoid breaking dev flow; just pass through
            logger.exception("DevAutoLoginMiddleware encountered an error")

        return self.get_response(request)

    @staticmethod
    def _allowed_path(path: str) -> bool:
        # Avoid interfering with admin, auth endpoints, API, and static/media
        disallowed_prefixes = (
            "/admin",
            "/api/",
            "/login",
            "/logout",
            settings.STATIC_URL or "/static/",
            settings.MEDIA_URL or "/media/",
        )
        return not any(path.startswith(p) for p in disallowed_prefixes)

    @staticmethod
    def _get_or_create_dev_user(request):
        """Get or create a dev user named 'devuser-<random_number>'.

        - Honors DEV_AUTO_LOGIN_USER if provided in settings
        - Persists the chosen dev username in session to avoid creating many users
        """
        User = get_user_model()  # noqa: N806
        try:
            # Prefer a specifically configured dev user
            target_username = getattr(settings, "DEV_AUTO_LOGIN_USER", "") or ""
            if target_username:
                user = User.objects.filter(username=target_username).first()
                if user is None:
                    user = User.objects.create(
                        username=target_username,
                        email=f"{target_username}@example.com",
                        computing_id=target_username,
                        first_name="Dev",
                        last_name="User",
                        is_active=True,
                        is_staff=False,
                    )
                request.session["DEV_AUTO_LOGIN_USER"] = user.username
                return user

            # Use a session-persisted dev username if available
            sess_username = request.session.get("DEV_AUTO_LOGIN_USER", "")
            if sess_username:
                user = User.objects.filter(username=sess_username).first()
                if user:
                    return user

            # Generate a new 'devuser-<random_number>' username and create it if not exists
            for _ in range(5):
                num = random.randint(1000, 999999)
                uname = f"devuser-{num}"
                user = User.objects.filter(username=uname).first()
                if user is None:
                    user = User.objects.create(
                        username=uname,
                        email=f"{uname}@example.com",
                        computing_id=uname,
                        first_name="Dev",
                        last_name="User",
                        is_active=True,
                        is_staff=False,
                    )
                    request.session["DEV_AUTO_LOGIN_USER"] = uname
                    return user

            # Fallback: reuse any existing devuser-* account
            user = (
                User.objects.filter(is_active=True, is_staff=False, username__startswith="devuser-")
                .order_by("?")
                .first()
            )
            if user:
                request.session["DEV_AUTO_LOGIN_USER"] = user.username
                return user
            return None
        except Exception:
            return None