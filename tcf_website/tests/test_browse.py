# pylint: disable=no-member
"""Tests for browse.py."""
from django.test import TestCase
from django.urls import reverse

from .test_utils import setup, suppress_request_warnings


class CourseViewTestCase(TestCase):
    """Tests for Course views."""

    def setUp(self):
        setup(self)

    @suppress_request_warnings
    def test_legacy_course_url_404(self):
        """Test if the legacy course view can handle wrong URLs"""
        url = reverse("course_legacy", args=[999999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_legacy_course_url_redirect(self):
        """Test if the legacy course view can handle redirects"""
        url = reverse("course_legacy", args=[self.course.id])
        response = self.client.get(url)
        self.assertRedirects(response, "/course/CS/1420/")

    def test_redirect_lowercase_mnemonic(self):
        """Test if course page URLs with lowercase mnemonics are redirected"""
        url = reverse("course", args=["cs", 1421])
        response = self.client.get(url)
        self.assertRedirects(response, "/course/CS/1421/")
