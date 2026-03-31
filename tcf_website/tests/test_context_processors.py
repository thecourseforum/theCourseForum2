# pylint: disable=no-member
"""Tests for template context processors."""

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from tcf_core.context_processors import base

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
