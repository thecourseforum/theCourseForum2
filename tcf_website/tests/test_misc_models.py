# pylint: disable=no-member
"""Tests for Misc. models that do not have many methods."""

from django.test import TestCase

from .test_utils import setup
from ..models import Vote


class MiscModelsTestCase(TestCase):
    """Tests for course model."""

    def setUp(self):
        setup(self)

    def test_school_name(self):
        """Test __str__ method in School model"""
        self.assertEqual("School of Hard Knocks", str(
            self.course.subject.department.school))

    def test_department_name(self):
        """Test __str__ method in Department model"""
        self.assertEqual("Computer Science", str(
            self.course.subject.department))

    def test_section_name(self):
        """Test __str__ method in Section mdoel"""
        self.assertEqual("CS 1420 | Software Testing | Fall 2020 | "
                         "Tom Jefferson (tjt3rea@virginia.edu)",
                         str(self.section_course))

    def test_course_grade_name(self):
        """Test __str__ method in CourseGrade model"""
        self.assertEqual("CS 1420 2.9", str(self.course_grade))

    def test_course_instructor_grade_name(self):
        """Test __str__ method in CourseInstructorGrade model"""
        self.assertEqual("Tom Jefferson CS 1420 3.8", str(
            self.instructor_grade))

    def test_course_vote_name(self):
        """Test __str__ method in Vote model"""
        vote = Vote.objects.create(
            value=-1,
            user=self.user4,
            review=self.review1)
        self.assertEqual(
            str(vote), "Vote of value -1 for Review by Taylor Comb "
            "(tcf2yay@virginia.edu) for CS 1420 | Software Testing taught by Tom Jefferson "
            "(tjt3rea@virginia.edu) by Kjell Kool ()")
