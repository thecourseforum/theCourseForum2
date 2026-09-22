"""Tests for template context processors."""

from datetime import UTC, datetime
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse

from tcf_core.context_processors import base, quick_rate_banner

from ..models import Schedule, ScheduledCourse
from .test_utils import setup


class BaseContextProcessorTestCase(TestCase):
    """``tcf_core.context_processors.base``."""

    def setUp(self):
        setup(self)
        self.factory = RequestFactory()

    def test_injects_debug_user_and_latest_semester(self):
        """Context includes DEBUG flag, request user, and Semester.latest()."""
        request = self.factory.get("/")
        request.user = AnonymousUser()
        ctx = base(request)
        self.assertEqual(ctx["DEBUG"], settings.DEBUG)
        self.assertIs(ctx["USER"], request.user)
        latest = ctx["LATEST_SEMESTER"]
        self.assertIsNotNone(latest)
        self.assertEqual(latest.pk, self.semester.pk)


class QuickRateBannerTests(TestCase):
    """The post-finals banner count."""

    def setUp(self):
        setup(self)
        schedule = Schedule.objects.create(
            name="Plan", user=self.user4, semester=self.semester
        )
        ScheduledCourse.objects.create(
            schedule=schedule,
            section=self.section_course2,
            instructor=self.instructor,
            time="",
        )
        self.factory = RequestFactory()

    def _request(self, user, path="/"):
        request = self.factory.get(path)
        request.user = user
        return request

    @patch("tcf_core.context_processors.timezone.now")
    def test_counts_candidates_in_a_banner_month(self, mock_now):
        mock_now.return_value = datetime(2026, 12, 15, tzinfo=UTC)
        context = quick_rate_banner(self._request(self.user4))
        self.assertEqual(context, {"quick_rate_banner_count": 1})

    @patch("tcf_core.context_processors.timezone.now")
    def test_silent_outside_banner_months(self, mock_now):
        mock_now.return_value = datetime(2026, 10, 15, tzinfo=UTC)
        self.assertEqual(quick_rate_banner(self._request(self.user4)), {})

    @patch("tcf_core.context_processors.timezone.now")
    def test_silent_for_anonymous_users(self, mock_now):
        mock_now.return_value = datetime(2026, 12, 15, tzinfo=UTC)
        self.assertEqual(quick_rate_banner(self._request(AnonymousUser())), {})

    @patch("tcf_core.context_processors.timezone.now")
    def test_silent_on_the_quick_rate_page(self, mock_now):
        mock_now.return_value = datetime(2026, 12, 15, tzinfo=UTC)
        request = self._request(self.user4, path=reverse("quick_rate"))
        self.assertEqual(quick_rate_banner(request), {})

    @patch("tcf_core.context_processors.timezone.now")
    def test_silent_on_the_schedule_page(self, mock_now):
        mock_now.return_value = datetime(2026, 12, 15, tzinfo=UTC)
        request = self._request(self.user4, path=reverse("schedule"))
        self.assertEqual(quick_rate_banner(request), {})

    @patch("tcf_core.context_processors.timezone.now")
    def test_count_is_cached_in_session_for_the_day(self, mock_now):
        mock_now.return_value = datetime(2026, 12, 15, tzinfo=UTC)
        request = self._request(self.user4)
        SessionMiddleware(lambda r: None).process_request(request)
        request.session.save()

        first = quick_rate_banner(request)
        self.assertEqual(first, {"quick_rate_banner_count": 1})

        with patch("tcf_core.context_processors.candidates_for") as mock_candidates:
            second = quick_rate_banner(request)

        mock_candidates.assert_not_called()
        self.assertEqual(second, first)
