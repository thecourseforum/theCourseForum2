"""Tests for browse views."""

from django.test import TestCase
from django.urls import reverse

from ..models import Club, ClubCategory, School
from .test_utils import setup, suppress_request_warnings


class CourseViewTestCase(TestCase):
    """Tests for Course views."""

    def setUp(self):
        setup(self)

    def test_redirect_lowercase_mnemonic(self):
        """Test if course page URLs with lowercase mnemonics are redirected"""
        url = reverse("course", args=["cs", 1421])
        response = self.client.get(url)
        self.assertRedirects(response, "/course/CS/1421/")

    @suppress_request_warnings
    def test_unknown_course_returns_404(self):
        """Unknown course should return 404."""
        url = reverse("course", args=["CS", 9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @suppress_request_warnings
    def test_unknown_department_returns_404(self):
        """Unknown department should return 404."""
        url = reverse("department", args=[999999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_browse_default_view_requires_featured_schools(self):
        """Default browse template expects CLAS and SEAS rows in the database."""
        School.objects.create(name="College of Arts & Sciences")
        School.objects.create(name="School of Engineering & Applied Science")
        response = self.client.get(reverse("browse"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["has_search"])

    def test_school_accordions_use_keyboard_accessible_buttons(self):
        """School headings expose native keyboard controls and accordion state."""
        clas = School.objects.create(name="College of Arts & Sciences")
        School.objects.create(name="School of Engineering & Applied Science")

        response = self.client.get(reverse("browse"))
        html = response.content.decode()

        self.assertRegex(
            html,
            rf'<h3 class="school-header__heading">\s*<button class="school-header '
            rf'[^\"]*"\s+id="school-{clas.pk}-toggle"',
        )
        self.assertIn('type="button"', html)
        self.assertIn('aria-expanded="false"', html)
        self.assertIn(f'aria-controls="school-{clas.pk}-departments"', html)
        self.assertIn(f'id="school-{clas.pk}-departments"', html)
        self.assertIn(f'aria-labelledby="school-{clas.pk}-toggle"', html)
        self.assertNotIn('<div class="school-header ', html)

    def test_school_accordion_toggle_updates_accessibility_state(self):
        """Accordion toggles keep ARIA and panel visibility in sync."""
        School.objects.create(name="College of Arts & Sciences")
        School.objects.create(name="School of Engineering & Applied Science")

        response = self.client.get(reverse("browse"))
        html = response.content.decode()

        self.assertIn("this.setAttribute('aria-expanded', String(willExpand));", html)
        self.assertIn("grid.hidden = !willExpand;", html)

    def test_browse_partial_results_returns_html(self):
        """XHR partial=results with search params returns results fragment."""
        response = self.client.get(
            reverse("browse"),
            {"title": "Software", "partial": "results"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"course-card", response.content)
        self.assertIn(b"data-browse-total", response.content)

    def test_browse_partial_no_search_returns_204(self):
        """XHR partial=results without search params returns 204."""
        response = self.client.get(
            reverse("browse"),
            {"partial": "results"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")

    def test_browse_partial_param_ignored_without_xhr(self):
        """partial=results without XHR still renders full browse page."""
        response = self.client.get(
            reverse("browse"),
            {"partial": "results", "title": "Software"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"browse-header", response.content)


class ClubBrowseAdvancedTestCase(TestCase):
    """Club browse filters and live-results partial (mode=clubs)."""

    def setUp(self):
        category = ClubCategory.objects.create(name="Arts", slug="arts")
        Club.objects.create(name="Photography Guild", category=category)
        Club.objects.create(name="Chess Club", category=category)

    def test_club_browse_search_by_name(self):
        """Filtered club browse returns matching rows."""
        response = self.client.get(
            reverse("browse"),
            {"mode": "clubs", "club_name": "Photo"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["has_search"])
        self.assertGreaterEqual(response.context["total"], 1)

    def test_club_browse_partial_results_returns_html(self):
        """XHR partial=results with club filters returns results fragment."""
        response = self.client.get(
            reverse("browse"),
            {"mode": "clubs", "club_name": "Photo", "partial": "results"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"data-browse-total", response.content)
        self.assertIn(b"search-result-card", response.content)

    def test_club_browse_partial_no_search_returns_204(self):
        """XHR partial=results without club search params returns 204."""
        response = self.client.get(
            reverse("browse"),
            {"mode": "clubs", "partial": "results"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
