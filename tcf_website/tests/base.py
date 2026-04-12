"""Reusable test base classes."""

from django.test import TestCase

from .test_utils import setup


class TCFDataTestCase(TestCase):
    """Loads shared catalog, users, reviews, and sections via ``test_utils.setup``."""

    def setUp(self):
        super().setUp()
        setup(self)
