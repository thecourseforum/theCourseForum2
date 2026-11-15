import json
import logging
import sys

from django.test import TestCase
from django.urls import reverse

from tcf_core.settings.request_log_middleware import (
    JsonFormatter,
    RequestIdFilter,
    TextFormatter,
    request_id_var,
)

from .test_utils import setup

LOGGER_NAME = "tcf_core.settings.request_log_middleware"
CLOUDFRONT_ID = "fake-cloudfront_id=="


class RequestLogMiddlewareTestCase(TestCase):
    def setUp(self):
        setup(self)

    def test_cloudfront_id_used(self):
        response = self.client.get(reverse("about"), HTTP_X_AMZ_CF_ID=CLOUDFRONT_ID)
        self.assertEqual(response.wsgi_request.request_id, CLOUDFRONT_ID)

    def test_missing_header_generates_id(self):
        response = self.client.get(reverse("about"))
        self.assertRegex(response.wsgi_request.request_id, r"^[0-9a-f]{32}$")

    def test_invalid_header_replaced(self):
        response = self.client.get(reverse("about"), HTTP_X_AMZ_CF_ID="bad id\tx")
        self.assertRegex(response.wsgi_request.request_id, r"^[0-9a-f]{32}$")

    def test_request_logged_once(self):
        with self.assertLogs(LOGGER_NAME, "INFO") as logs:
            self.client.get(reverse("about"))
        self.assertEqual(len(logs.records), 1)
        record = logs.records[0]
        self.assertEqual(record.method, "GET")
        self.assertEqual(record.path, reverse("about"))
        self.assertEqual(record.status, 200)
        self.assertIsInstance(record.duration_ms, int)
        self.assertIsNone(record.user_id)

    def test_logged_in_user_id_logged(self):
        self.client.force_login(self.user1)
        with self.assertLogs(LOGGER_NAME, "INFO") as logs:
            self.client.get(reverse("about"))
        self.assertEqual(logs.records[0].user_id, str(self.user1.pk))

    def test_not_found_logged_by_request_line_only(self):
        with self.assertLogs(LOGGER_NAME, "INFO") as logs:
            self.client.get("/no-such-page/")
        self.assertEqual(logs.records[0].status, 404)
        self.assertEqual(logging.getLogger("django.request").level, logging.ERROR)

    def test_health_check_not_logged(self):
        with self.assertNoLogs(LOGGER_NAME, "INFO"):
            response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

    def test_request_id_reset_after_response(self):
        self.client.get(reverse("about"), HTTP_X_AMZ_CF_ID=CLOUDFRONT_ID)
        self.assertEqual(request_id_var.get(), "-")


class JsonFormatterTestCase(TestCase):
    def _format(self, **extra):
        record = logging.LogRecord(
            "tcf.test", logging.WARNING, __file__, 1, "hello %s", ("world",), None
        )
        for key, value in extra.items():
            setattr(record, key, value)
        RequestIdFilter().filter(record)
        return json.loads(JsonFormatter().format(record))

    def test_base_fields(self):
        self.assertEqual(
            self._format(),
            {
                "level": "WARNING",
                "logger": "tcf.test",
                "request_id": "-",
                "message": "hello world",
            },
        )

    def test_request_id_from_context(self):
        token = request_id_var.set("abc")
        try:
            self.assertEqual(self._format()["request_id"], "abc")
        finally:
            request_id_var.reset(token)

    def test_request_id_from_record_request(self):
        request = type("Request", (), {"request_id": "from-request"})()
        self.assertEqual(self._format(request=request)["request_id"], "from-request")

    def test_request_fields_included(self):
        payload = self._format(method="GET", path="/x/", status=200)
        self.assertEqual(payload["method"], "GET")
        self.assertEqual(payload["path"], "/x/")
        self.assertEqual(payload["status"], 200)


class TextFormatterTestCase(TestCase):
    def _format(self, exc_info=None, **extra):
        record = logging.LogRecord(
            "tcf.test", logging.INFO, __file__, 1, "hello %s", ("world",), exc_info
        )
        for key, value in extra.items():
            setattr(record, key, value)
        return TextFormatter().format(record)

    def test_plain_message(self):
        self.assertEqual(self._format(), "INFO tcf.test: hello world")

    def test_request_line(self):
        line = self._format(
            method="GET", path="/about/", status=200, duration_ms=12, user_id=None
        )
        self.assertEqual(line, "INFO GET /about/ 200 12ms")

    def test_request_line_with_user(self):
        line = self._format(
            method="GET", path="/about/", status=200, duration_ms=12, user_id="7"
        )
        self.assertEqual(line, "INFO GET /about/ 200 12ms user=7")

    def test_request_id_shortened(self):
        line = self._format(
            request_id=CLOUDFRONT_ID,
            method="GET",
            path="/about/",
            status=200,
            duration_ms=12,
            user_id=None,
        )
        self.assertEqual(line, f"INFO [{CLOUDFRONT_ID[:8]}] GET /about/ 200 12ms")

    def test_request_id_on_plain_message(self):
        self.assertEqual(
            self._format(request_id=CLOUDFRONT_ID),
            f"INFO [{CLOUDFRONT_ID[:8]}] tcf.test: hello world",
        )

    def test_no_request_id_outside_request(self):
        self.assertEqual(self._format(request_id="-"), "INFO tcf.test: hello world")

    def test_traceback_multiline(self):
        try:
            raise ValueError("boom")
        except ValueError:
            output = self._format(exc_info=sys.exc_info())
        self.assertIn("\nTraceback (most recent call last):\n", output)
