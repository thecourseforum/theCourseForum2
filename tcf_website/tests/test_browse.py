"""Tests for browse.py."""
from django.http import Http404
from django.test import TestCase
from django.urls import reverse

from .test_utils import setup


class CourseViewTestCase(TestCase):
    """Tests for Course views."""

    def setUp(self):
        setup(self)

    def test_legacy_course_url_404(self):
        url = reverse('course_legacy', args=[999999])
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

    def test_legacy_course_url_redirect(self):
        url = reverse('course_legacy', args=[self.course.id])
        response = self.client.get(url)
        self.assertRedirects(response, '/course/CS/420')

    def test_redirect_lowercase_mnemonic(self):
        url = reverse('course', args=['cs', 421])
        response = self.client.get(url)
        self.assertRedirects(response, '/course/CS/421')
