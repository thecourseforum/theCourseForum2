# pylint: disable=no-member
"""Smoke tests for top-level and static-ish pages."""

from django.test import TestCase
from django.urls import reverse


class LandingAndInfoPagesTestCase(TestCase):
    """Index, about, legal pages return successfully."""

    def test_index_ok(self):
        """Home page renders."""
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["mode"], "courses")

    def test_index_clubs_mode(self):
        """Landing page honors mode=clubs."""
        response = self.client.get(reverse("index"), {"mode": "clubs"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["mode"], "clubs")
        self.assertEqual(response.context["mode_noun"], "club")
        self.assertIsInstance(response.context["landing_spotlight_reviews"], list)

    def test_index_spotlight_reviews_context(self):
        """Landing page exposes recent reviews list for default course mode."""
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["landing_spotlight_reviews"], list)

    def test_about_ok(self):
        """About page renders."""
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)

    def test_privacy_ok(self):
        """Privacy page renders."""
        response = self.client.get(reverse("privacy"))
        self.assertEqual(response.status_code, 200)

    def test_terms_ok(self):
        """Terms page renders."""
        response = self.client.get(reverse("terms"))
        self.assertEqual(response.status_code, 200)
