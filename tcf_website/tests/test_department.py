# pylint: disable=no-member
"""Tests for Department model."""

from django.test import TestCase

from ..models import Vote
from .test_utils import setup


class DepartmentTestCase(TestCase):
    """Tests for Department model."""

    def setUp(self):
        setup(self)
