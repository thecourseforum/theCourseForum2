# pylint: disable=no-member
"""Tests for Instructor model with edge cases."""

from django.test import TestCase
from django.urls import reverse

from .test_utils import setup, suppress_request_warnings


class InstructorEdgeTestCase(TestCase):
    """Tests for instructor model with edge cases."""

    def setUp(self):
        setup(self)

    def test_average_rating_for_course_no_reviews(self):
        """Test average rating for a particular course when there are no reviews."""
        self.review1.delete()
        self.review2.delete()

        self.assertIsNone(
            self.instructor.average_rating_for_course(self.course)
        )

    def test_average_difficulty_for_course_no_reviews(self):
        """Test average difficulty for a particular course when there are no reviews."""
        self.review1.delete()
        self.review2.delete()

        self.assertIsNone(
            self.instructor.average_rating_for_course(self.course)
        )

    def test_average_enjoyability_for_course_no_reviews(self):
        """Test average enjoyability for a particular course when there are no reviews."""
        self.review1.delete()
        self.review2.delete()

        self.assertIsNone(
            self.instructor.average_enjoyability_for_course(self.course)
        )

    def test_average_instructor_rating_for_course_no_reviews(self):
        """Test average instructor rating for a particular course when there are no reviews."""
        self.review1.delete()
        self.review2.delete()

        self.assertIsNone(
            self.instructor.average_instructor_rating_for_course(self.course)
        )

    def test_average_recommendability_for_course_no_reviews(self):
        """Test average recommendability for a particular course when there are no reviews."""
        self.review1.delete()
        self.review2.delete()

        self.assertIsNone(
            self.instructor.average_recommendability_for_course(self.course)
        )

    def test_average_hours_for_course_no_reviews(self):
        """Test average hours for a particular course when there are no reviews."""
        self.review1.delete()
        self.review2.delete()

        self.assertIsNone(self.instructor.average_hours_for_course(self.course))

    def test_average_reading_hours_for_course_no_reviews(self):
        """Test average reading hours for a particular course when there are no reviews."""
        self.review1.delete()
        self.review2.delete()

        self.assertIsNone(
            self.instructor.average_reading_hours_for_course(self.course)
        )

    def test_average_writing_hours_for_course_no_reviews(self):
        """Test average reading hours for a particular course when there are no reviews."""
        self.review1.delete()
        self.review2.delete()

        self.assertIsNone(
            self.instructor.average_writing_hours_for_course(self.course)
        )

    def test_average_group_hours_for_course_no_reviews(self):
        """Test average group hours for a particular course when there are no reviews."""
        self.review1.delete()
        self.review2.delete()

        self.assertIsNone(
            self.instructor.average_group_hours_for_course(self.course)
        )

    def test_average_other_hours_for_course_no_reviews(self):
        """Test average other hours for a particular course when there are no reviews."""
        self.review1.delete()
        self.review2.delete()

        self.assertIsNone(
            self.instructor.average_other_hours_for_course(self.course)
        )

    def test_average_gpa_for_course_no_grades(self):
        """Test average gpa for a particular course when there are no grades."""
        self.instructor_grade.delete()
        self.instructor_grade2.delete()

        self.assertIsNone(self.instructor.average_gpa_for_course(self.course))

    def test_average_difficulty_no_reviews(self):
        """Test average difficulty for all instructor's courses when there are no reviews."""
        self.assertIsNone(self.instructor2.average_difficulty())

    def test_taught_courses_none(self):
        """Test taught courses when there are none."""
        self.assertFalse(self.instructor2.taught_courses().exists())

    def test_average_rating_attribute_missing(self):
        """Test average rating for all courses of an
        instructor when an attribute (or more) is missing"""
        self.assertIsNone(self.instructor2.average_rating())

    def test_average_gpa_no_grades(self):
        """Test average gpa for all of the courses of an
        instructor instructor when there are no grades"""
        self.instructor_grade.delete()
        self.instructor_grade2.delete()
        self.instructor_grade3.delete()

        self.assertIsNone(self.instructor.average_gpa())

    def test_instructor_name_no_email(self):
        """Test __str__ method in Instructor model when there is no email"""
        self.assertEqual("No Email ()", str(self.instructor2))

    @suppress_request_warnings
    def test_instructor_view_404(self):
        """Test if instructor view returns a 404 status code when it should."""
        response = self.client.post(reverse("instructor", args=(99999999999,)))
        self.assertEqual(response.status_code, 404)
