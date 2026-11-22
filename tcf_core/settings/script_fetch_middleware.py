import logging

from django.conf import settings
from django.http import HttpResponseForbidden

from tcf_website.search.browse_helpers import is_browse_results_partial_request

logger = logging.getLogger(__name__)


def _is_script_request(request) -> bool:
    mode = request.headers.get("Sec-Fetch-Mode")
    return (
        request.headers.get("Sec-Fetch-Dest") == "empty"
        and mode is not None
        and mode != "navigate"
    )


def _is_anonymous_allowed(request) -> bool:
    return (
        request.path == "/search/"
        and request.headers.get("X-Requested-With") == "XMLHttpRequest"
    ) or (request.path == "/browse/" and is_browse_results_partial_request(request))


class ScriptFetchLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        mode = settings.SCRIPT_FETCH_LOGIN
        if (
            mode == "off"
            or not _is_script_request(request)
            or request.user.is_authenticated
            or _is_anonymous_allowed(request)
        ):
            return self.get_response(request)

        logger.warning(
            "Anonymous script request: method=%s path=%s xff=%s ua=%s "
            "sec_fetch_mode=%s sec_fetch_site=%s",
            request.method,
            request.get_full_path(),
            request.headers.get("X-Forwarded-For", ""),
            request.headers.get("User-Agent", ""),
            request.headers.get("Sec-Fetch-Mode", ""),
            request.headers.get("Sec-Fetch-Site", ""),
        )
        if mode == "enforce":
            return HttpResponseForbidden("Log in to use this feature.")
        return self.get_response(request)
