# pylint: disable=no-member

"""Tests for Semester model."""

from django.test import TestCase
from ..models import Semester
from .test_utils import setup


class IsAfterTestCase(TestCase):
    """Tests for is_after method."""
    def setUp(self):
        pass

    def test_is_after(self):
        """When caller is after."""
        first = Semester(season='FALL', year=2019, number=1198)
        second = Semester(season='JANUARY', year=2020, number=1201)

        self.assertTrue(second.is_after(first))
        self.assertFalse(first.is_after(second))

    def test_same(self):
        """Identical semesters."""
        first = Semester(season='FALL', year=2019, number=1198)
        second = Semester(season='FALL', year=2019, number=1198)

        self.assertFalse(first.is_after(second))

    def test_before(self):
        """Test caller is before."""
        first = Semester(season='FALL', year=2019, number=1198)
        second = Semester(season='JANUARY', year=2020, number=1201)

        self.assertFalse(first.is_after(second))


class SemesterTestCase(TestCase):
    """Additional Tests for Semester Model"""
    def setUp(self):
        setup(self)

    def test_repr(self):
        """Test for repr method"""
        repr_expected = "2020 Fall (1208)"
        self.assertEqual(repr(self.semester), repr_expected)

    def test_repr_missing_info(self):
        """Test for repr method when information is missing"""
        repr_expected = "2019  (1198)"
        self.assertEqual(repr(self.incomplete_semester), repr_expected)
