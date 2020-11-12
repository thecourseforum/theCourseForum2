# pylint: disable=no-member
"""Tests for Instructor model."""

from django.test import TestCase

from .test_utils import setup


class InstructorTestCase(TestCase):
    """Tests for instructor model."""

    def setUp(self):
        setup(self)

    def test_full_name(self):
        """Course full name string."""
        self.assertTrue(self.instructor.full_name() == "Tom Jefferson")

    def test_average_rating(self):
        """Test average rating."""

        rating = (self.review1.recommendability +
                  self.review2.recommendability +
                  self.review1.instructor_rating +
                  self.review2.instructor_rating +
                  self.review1.enjoyability +
                  self.review2.enjoyability) / 6

        self.assertTrue(
            self.instructor.average_rating_for_course(self.course) ==
            rating)

    def test_average_difficulty(self):
        """Test average difficulty."""

        difficulty = (self.review1.difficulty +
                      self.review2.difficulty) / 2

        self.assertTrue(
            self.instructor.average_difficulty_for_course(self.course) ==
            difficulty)

    def test_average_rating_no_reviews(self):
        """Test average rating no reviews."""
        self.review1.delete()
        self.review2.delete()

        self.assertTrue(
            self.instructor.average_rating_for_course(self.course) is
            None)

    def test_average_difficulty_no_reviews(self):
        """Test average difficulty no reviews."""

        self.review1.delete()
        self.review2.delete()

        self.assertTrue(
            self.instructor.average_rating_for_course(self.course) is
            None)
