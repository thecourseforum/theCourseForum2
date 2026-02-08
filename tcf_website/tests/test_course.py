# pylint: disable=no-member
"""Tests for Course model."""

from django.test import TestCase

from ..models import Semester
from .test_utils import setup


class CourseTestCase(TestCase):
    """Tests for course model."""

    def setUp(self):
        setup(self)

    def test_review_count(self):
        """Test review count method"""
        self.assertEqual(self.course.review_count(), 2)

    def test_code(self):
        """Course code string."""
        code = self.course.code()
        self.assertEqual(code, "CS 1420")

    def test_is_recent(self):
        """Test for is_recent()."""
        self.assertTrue(self.course.is_recent())

        Semester.objects.create(year=2021, season="JANUARY", number=1211)

        self.assertFalse(self.course.is_recent())

    def test_average_rating(self):
        """Test average rating."""
        rating = (self.review1.average() + self.review2.average()) / 2

        self.assertAlmostEqual(self.course.average_rating(), rating, 4)

    def test_average_difficulty(self):
        """Test average difficulty."""
        difficulty = (self.review1.difficulty + self.review2.difficulty) / 2

        self.assertAlmostEqual(self.course.average_difficulty(), difficulty, 4)

    def test_average_rating_no_reviews(self):
        """Test average rating no reviews."""
        self.review1.delete()
        self.review2.delete()

        self.assertIsNone(self.course.average_rating())

    def test_average_difficulty_no_reviews(self):
        """Test average difficulty no reviews."""
        self.review1.delete()
        self.review2.delete()

        self.assertIsNone(self.course.average_difficulty())

    def test_student_eval_link(self):
        """Test if a student eval link matches up with a real link."""
        eval_link = (
            "https://evals.itc.virginia.edu/"
            + "course-selectionguide/pages/SGMain.jsp?cmp=CS,1420"
        )
        # need to break into 2 lines because otherwise pylint gets mad
        # this link doesn't actually work because CS 420 is not a real class
        self.assertEqual(eval_link, self.course.eval_link())

    def test_prerequisites_default(self):
        """Test that prerequisites field defaults to empty list."""
        self.assertEqual(self.course.prerequisites, [])

    def test_prerequisites_set_and_get(self):
        """Test that prerequisites can be set and retrieved."""
        prerequisites = ["CS 1110", "CS 2100"]
        self.course.prerequisites = prerequisites
        self.course.save()
        # Refresh from database
        self.course.refresh_from_db()
        self.assertEqual(self.course.prerequisites, prerequisites)
