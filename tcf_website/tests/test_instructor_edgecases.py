# pylint: disable=no-member
"""Tests for Instructor model with edge cases."""

from django.test import TestCase

from .test_utils import setup


class InstructorEdgeTestCase(TestCase):
    """Tests for instructor model with edge cases."""

    def setUp(self):
        setup(self)

    def test_average_rating_for_course_no_reviews(self):
        """Test average rating for a particular course when there are no reviews."""

        self.review1.delete()
        self.review2.delete()

        self.assertTrue(
            self.instructor.average_rating_for_course(self.course) is
            None)

    def test_average_difficulty_for_course_no_reviews(self):
        """Test average difficulty for a particular course when there are no reviews."""

        self.review1.delete()
        self.review2.delete()

        self.assertTrue(
            self.instructor.average_rating_for_course(self.course) is
            None)

    def test_average_enjoyability_for_course_no_reviews(self):
        """Test average enjoyability for a particular course when there are no reviews."""

        self.review1.delete()
        self.review2.delete()

        self.assertTrue(
            self.instructor.average_enjoyability_for_course(self.course) is
            None)

    def test_average_instructor_rating_for_course_no_reviews(self):
        """Test average instructor rating for a particular course when there are no reviews."""

        self.review1.delete()
        self.review2.delete()

        self.assertTrue(
            self.instructor.average_instructor_rating_for_course(
                self.course) is None)

    def test_average_recommendability_for_course_no_reviews(self):
        """Test average recommendability for a particular course when there are no reviews."""

        self.review1.delete()
        self.review2.delete()

        self.assertTrue(
            self.instructor.average_recommendability_for_course(
                self.course) is None)

    def test_average_hours_for_course_no_reviews(self):
        """Test average hours for a particular course when there are no reviews."""

        self.review1.delete()
        self.review2.delete()

        self.assertTrue(
            self.instructor.average_hours_for_course(
                self.course) is None)

    def test_average_reading_hours_for_course_no_reviews(self):
        """Test average reading hours for a particular course when there are no reviews."""

        self.review1.delete()
        self.review2.delete()

        self.assertTrue(
            self.instructor.average_reading_hours_for_course(
                self.course) is None)

    def test_average_writing_hours_for_course_no_reviews(self):
        """Test average reading hours for a particular course when there are no reviews."""

        self.review1.delete()
        self.review2.delete()

        self.assertTrue(
            self.instructor.average_writing_hours_for_course(
                self.course) is None)

    def test_average_group_hours_for_course_no_reviews(self):
        """Test average group hours for a particular course when there are no reviews."""

        self.review1.delete()
        self.review2.delete()

        self.assertTrue(
            self.instructor.average_group_hours_for_course(
                self.course) is None)

    def test_average_other_hours_for_course_no_reviews(self):
        """Test average other hours for a particular course when there are no reviews."""

        self.review1.delete()
        self.review2.delete()

        self.assertTrue(
            self.instructor.average_other_hours_for_course(
                self.course) is None)

    def test_average_gpa_for_course_no_grades(self):
        """Test average gpa for a particular course when there are no grades."""

        self.instructor_grade.delete()
        self.instructor_grade2.delete()

        self.assertTrue(
            self.instructor.average_gpa_for_course(
                self.course) is None)

    def test_average_difficulty_no_reviews(self):
        """Test average difficulty for all instructor's courses when there are no reviews."""

        self.assertTrue(self.instructor2.average_difficulty() is None)

    def test_taught_courses_none(self):
        """Test taught courses when there are none."""

        courses_taught = "<QuerySet []>"
        self.assertEqual(
            str(self.instructor2.taught_courses()), courses_taught)

    def test_average_rating_attribute_missing(self):
        """Test average rating for all courses of an
        instructor when an attribute (or more) is missing"""

        self.assertTrue(self.instructor2.average_rating() is None)

    def test_average_gpa_no_grades(self):
        """Test average gpa for all of the courses of an
        instructor instructor when there are no grades"""

        self.instructor_grade.delete()
        self.instructor_grade2.delete()
        self.instructor_grade3.delete()

        self.assertTrue(self.instructor.average_gpa() is None)

    def test_instructor_name(self):
        """Test __str__ method in Instructor model when there is an email"""
        self.assertEqual(
            "Tom Jefferson (tjt3rea@virginia.edu)", str(self.instructor))

    def test_instructor_name_no_email(self):
        """Test __str__ method in Instructor model when there is no email"""
        self.assertEqual(
            "No Email ()", str(self.instructor2))
