# pylint: disable=no-member
"""Tests for Course model."""

from django.test import TestCase

from ..models import Semester
from .test_utils import setup


class CourseTestCase(TestCase):
    """Tests for course model."""

    def setUp(self):
        setup(self)

    def test_code(self):
        """Course code string."""
        code = self.course.code()
        self.assertTrue(code == 'CS 420')

    def test_is_recent(self):
        """Test for is_recent()."""

        self.assertTrue(self.course.is_recent())

        Semester.objects.create(
            year=2021,
            season='JANUARY',
            number=1211
        )

        self.assertFalse(self.course.is_recent())

    def test_average_rating(self):
        """Test average rating."""

        rating = (self.review1.average() +
                  self.review2.average()) / 2

        self.assertTrue(self.course.average_rating() == rating)

    def test_average_difficulty(self):
        """Test average difficulty."""

        difficulty = (self.review1.difficulty +
                      self.review2.difficulty) / 2

        self.assertTrue(self.course.average_difficulty() == difficulty)

    def test_average_rating_no_reviews(self):
        """Test average rating no reviews."""
        self.review1.delete()
        self.review2.delete()

        self.assertTrue(self.course.average_rating() is None)

    def test_average_difficulty_no_reviews(self):
        """Test average difficulty no reviews."""

        self.review1.delete()
        self.review2.delete()

        self.assertTrue(self.course.average_difficulty() is None)
