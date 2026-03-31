# pylint: disable=no-member
"""Tests for small helpers in ``tcf_website.utils``."""

from django.test import RequestFactory, TestCase
from django.urls import reverse

from tcf_website.utils import parse_mode, safe_next_url, safe_round


class ParseModeTestCase(TestCase):
    """GET mode parsing for search / landing."""

    def test_default_is_courses(self):
        """No mode param means course search context."""
        factory = RequestFactory()
        request = factory.get("/search/")
        mode, is_club = parse_mode(request)
        self.assertEqual(mode, "courses")
        self.assertFalse(is_club)

    def test_clubs_mode(self):
        """mode=clubs sets club flag for search UI."""
        factory = RequestFactory()
        request = factory.get("/search/", {"mode": "clubs"})
        mode, is_club = parse_mode(request)
        self.assertEqual(mode, "clubs")
        self.assertTrue(is_club)


class SafeRoundTestCase(TestCase):
    """``safe_round`` null and float handling."""

    def test_rounds_float(self):
        """Numeric values round to two decimals."""
        self.assertEqual(safe_round(3.14159), 3.14)

    def test_none_returns_em_dash(self):
        """Missing stats render as an em dash."""
        self.assertEqual(safe_round(None), "\u2014")


class SafeNextUrlTestCase(TestCase):
    """Open-redirect protection for schedule/review flows."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_missing_next_returns_default(self):
        """Without next param, return the fallback URL."""
        request = self.factory.post(reverse("schedule"))
        self.assertEqual(
            safe_next_url(request, reverse("index")),
            reverse("index"),
        )

    def test_valid_relative_next_is_returned(self):
        """Same-host relative next URLs are accepted."""
        path = reverse("browse")
        request = self.factory.post(
            reverse("schedule"),
            {"next": path},
            HTTP_HOST="testserver",
        )
        self.assertEqual(safe_next_url(request, reverse("index")), path)
