from django.test import TestCase, override_settings
from django.urls import reverse

from .test_utils import setup, suppress_request_warnings

SCRIPT_HEADERS = {"HTTP_SEC_FETCH_MODE": "cors", "HTTP_SEC_FETCH_DEST": "empty"}
XHR_HEADERS = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
LOGGER_NAME = "tcf_core.settings.script_fetch_middleware"


@override_settings(SCRIPT_FETCH_LOGIN="enforce")
class ScriptFetchLoginTestCase(TestCase):
    def setUp(self):
        setup(self)
        self.page_url = reverse(
            "course_instructor", args=[self.course2.id, self.instructor.id]
        )

    @suppress_request_warnings
    def test_anon_cors_fetch_blocked(self):
        response = self.client.get(self.page_url, **SCRIPT_HEADERS)
        self.assertEqual(response.status_code, 403)

    @suppress_request_warnings
    def test_anon_same_origin_fetch_blocked(self):
        response = self.client.get(
            self.page_url,
            HTTP_SEC_FETCH_MODE="same-origin",
            HTTP_SEC_FETCH_DEST="empty",
        )
        self.assertEqual(response.status_code, 403)

    def test_anon_navigation_allowed(self):
        response = self.client.get(
            self.page_url,
            HTTP_SEC_FETCH_MODE="navigate",
            HTTP_SEC_FETCH_DEST="document",
        )
        self.assertEqual(response.status_code, 200)

    def test_anon_no_sec_fetch_headers_allowed(self):
        response = self.client.get(self.page_url)
        self.assertEqual(response.status_code, 200)

    def test_logged_in_fetch_allowed(self):
        self.client.force_login(self.user1)
        response = self.client.get(self.page_url, **SCRIPT_HEADERS)
        self.assertEqual(response.status_code, 200)

    def test_anon_search_autocomplete_allowed(self):
        response = self.client.get(
            reverse("search"),
            {"q": self.subdepartment.mnemonic},
            **SCRIPT_HEADERS,
            **XHR_HEADERS,
        )
        self.assertEqual(response.status_code, 200)

    @suppress_request_warnings
    def test_anon_search_without_xrw_blocked(self):
        response = self.client.get(
            reverse("search"),
            {"q": self.subdepartment.mnemonic},
            **SCRIPT_HEADERS,
        )
        self.assertEqual(response.status_code, 403)

    def test_anon_browse_partial_allowed(self):
        response = self.client.get(
            reverse("browse"),
            {"title": "x", "partial": "results"},
            **SCRIPT_HEADERS,
            **XHR_HEADERS,
        )
        self.assertEqual(response.status_code, 200)

    @suppress_request_warnings
    def test_anon_browse_full_page_blocked(self):
        response = self.client.get(reverse("browse"), **SCRIPT_HEADERS, **XHR_HEADERS)
        self.assertEqual(response.status_code, 403)

    def test_anon_iframe_navigation_allowed(self):
        response = self.client.get(
            self.page_url,
            HTTP_SEC_FETCH_MODE="navigate",
            HTTP_SEC_FETCH_DEST="iframe",
        )
        self.assertEqual(response.status_code, 200)

    @override_settings(SCRIPT_FETCH_LOGIN="log")
    def test_log_mode_serves_and_logs(self):
        with self.assertLogs(LOGGER_NAME, "WARNING") as logs:
            response = self.client.get(self.page_url, **SCRIPT_HEADERS)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(logs.records), 1)

    @override_settings(SCRIPT_FETCH_LOGIN="off")
    def test_off_mode_serves_without_logging(self):
        with self.assertNoLogs(LOGGER_NAME, "WARNING"):
            response = self.client.get(self.page_url, **SCRIPT_HEADERS)
        self.assertEqual(response.status_code, 200)
