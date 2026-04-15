"""Tests for shared URL and mode helpers."""

from html import unescape
from urllib.parse import parse_qs, urlsplit

from django.template import Context, Template
from django.test import RequestFactory, TestCase
from django.urls import reverse

from tcf_website.utils import (
    parse_mode,
    safe_next_url,
    safe_round,
    update_query_params,
    with_mode,
)


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

    def test_none_returns_none(self):
        """Missing stats return None so templates handle display via {% else %}—{% endif %}."""
        self.assertIsNone(safe_round(None))


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


class QueryParamHelperTestCase(TestCase):
    """Querystring helpers used by views and template tags."""

    def test_update_query_params_adds_and_removes_values(self):
        """Helper should merge params and drop cleared keys."""
        url = update_query_params("/browse/?q=test&page=2", page=None, mode="clubs")
        self.assertEqual(url, "/browse/?q=test&mode=clubs")

    def test_with_mode_omits_default_courses_mode(self):
        """Course mode should not be serialized into URLs."""
        self.assertEqual(with_mode("/browse/?q=test", "courses"), "/browse/?q=test")

    def test_with_mode_serializes_clubs_mode(self):
        """Club mode should be preserved explicitly."""
        self.assertEqual(with_mode("/browse/", "clubs"), "/browse/?mode=clubs")


class ModeUrlTemplateTagTestCase(TestCase):
    """Template tags should centralize mode-aware navigation."""

    def setUp(self):
        self.factory = RequestFactory()

    def _render(self, template_string, request, **context):
        return Template("{% load custom_tags %}" + template_string).render(
            Context({"request": request, **context})
        )

    def _assert_url(self, rendered: str, expected_path: str, expected_query: dict):
        """Compare rendered template tag output as a URL, not escaped HTML."""
        parsed = urlsplit(unescape(rendered))
        self.assertEqual(parsed.path, expected_path)
        self.assertEqual(parse_qs(parsed.query), expected_query)

    def test_mode_url_preserves_current_club_mode(self):
        """Mode-aware browse links should keep the current club context."""
        request = self.factory.get("/?mode=clubs")
        rendered = self._render("{% mode_url request 'browse' %}", request)
        self._assert_url(rendered, reverse("browse"), {"mode": ["clubs"]})

    def test_mode_url_supports_explicit_query_params(self):
        """Review links should combine mode preservation with explicit query params."""
        request = self.factory.get("/?mode=clubs")
        rendered = self._render(
            "{% mode_url request 'new_review' query_club=club_id %}",
            request,
            club_id=12,
        )
        self._assert_url(
            rendered,
            reverse("new_review"),
            {"mode": ["clubs"], "club": ["12"]},
        )

    def test_mode_url_can_force_club_mode(self):
        """Club destinations should opt into club mode explicitly."""
        request = self.factory.get("/")
        rendered = self._render(
            "{% mode_url request 'club' category_slug=category club_id=club_id mode='clubs' %}",
            request,
            category="CS",
            club_id=7,
        )
        self._assert_url(rendered, reverse("club", args=["CS", 7]), {"mode": ["clubs"]})
