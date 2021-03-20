# pylint: disable=no-member
"""Tests for Instructor model."""

from django.test import TestCase
from django.urls import reverse

from .test_utils import setup, suppress_request_warnings
from ..views.browse import safe_round


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

    def test_instructor_view(self):
        """Test if context variables are correct in the instructor view."""
        response = self.client.post(
            reverse('instructor', args=(self.instructor.id,)))
        difficulty = safe_round(self.instructor.average_difficulty())
        rating = safe_round(self.instructor.average_rating())
        self.assertEqual(difficulty, response.context[0]['avg_difficulty'])
        self.assertEqual(rating, response.context[0]['avg_rating'])

    @suppress_request_warnings
    def test_instructor_view_404(self):
        """Test if instructor view returns a 404 status code when it should."""
        response = self.client.post(
            reverse('instructor', args=(99999999999,)))
        self.assertEqual(response.status_code, 404)
