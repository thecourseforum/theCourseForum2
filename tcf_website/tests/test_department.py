# pylint: disable=no-member
"""Tests for Department model."""

from random import choice, randint
from unittest.mock import MagicMock

from django.test import TestCase

from ..models import Course
from .test_utils import create_new_semester, setup


class DepartmentTestCase(TestCase):
    """Tests for Department model."""

    def setUp(self):
        setup(self)

    def test_department_name(self):
        """Test Department model __str__ method"""
        self.assertEqual(str(self.department), "Computer Science")
