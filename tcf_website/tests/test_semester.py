"""Tests for Semester model."""

from datetime import datetime

from django.test import TestCase

from ..models import Semester
from .test_utils import setup


class IsAfterTestCase(TestCase):
    """Tests for is_after method."""

    def setUp(self):
        pass

    def test_is_after(self):
        """When caller is after."""
        first = Semester(season="FALL", year=2019, number=1198)
        second = Semester(season="JANUARY", year=2020, number=1201)

        self.assertTrue(second.is_after(first))
        self.assertFalse(first.is_after(second))

    def test_same(self):
        """Identical semesters."""
        first = Semester(season="FALL", year=2019, number=1198)
        second = Semester(season="FALL", year=2019, number=1198)

        self.assertFalse(first.is_after(second))

    def test_before(self):
        """Test caller is before."""
        first = Semester(season="FALL", year=2019, number=1198)
        second = Semester(season="JANUARY", year=2020, number=1201)

        self.assertFalse(first.is_after(second))


class SemesterTestCase(TestCase):
    """Additional Tests for Semester Model"""

    def setUp(self):
        setup(self)

    def test_repr(self):
        """Test for __repr__ method"""
        self.assertEqual(repr(self.semester), "2025 Fall (1258)")

    def test_repr_missing_info(self):
        """Test for __repr__ method when information is missing"""
        self.assertEqual(repr(self.incomplete_semester), "2023  (1238)")

    def test_latest_returns_highest_semester_number(self):
        """``latest()`` picks the term with the greatest SIS number."""
        self.assertEqual(Semester.latest().pk, self.semester.pk)


class HasStartedTestCase(TestCase):
    """Tests for the date-based ``has_started`` gate."""

    # Reference "now": July 8, 2026.
    AS_OF = datetime(2026, 7, 8)

    def test_past_year_has_started(self):
        """A term from an earlier year has always started."""
        sem = Semester(season="FALL", year=2020, number=1208)
        self.assertTrue(sem.has_started(as_of=self.AS_OF))

    def test_future_year_has_not_started(self):
        """A term in a later year has not started."""
        sem = Semester(season="SPRING", year=2030, number=1302)
        self.assertFalse(sem.has_started(as_of=self.AS_OF))

    def test_fall_this_year_not_started_before_august(self):
        """Fall 2026 has not started as of July 2026 (classes begin in August)."""
        sem = Semester(season="FALL", year=2026, number=1268)
        self.assertFalse(sem.has_started(as_of=self.AS_OF))

    def test_summer_this_year_started_by_july(self):
        """Summer 2026 has started as of July 2026 (classes begin in May)."""
        sem = Semester(season="SUMMER", year=2026, number=1266)
        self.assertTrue(sem.has_started(as_of=self.AS_OF))

    def test_start_month_boundary_is_inclusive(self):
        """A term is considered started once its start month is reached."""
        sem = Semester(season="FALL", year=2026, number=1268)
        self.assertTrue(sem.has_started(as_of=datetime(2026, 8, 1)))
