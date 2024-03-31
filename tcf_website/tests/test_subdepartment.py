# pylint: disable=no-member
"""Tests for Course model."""

from django.test import TestCase

from ..models import Course
from .test_utils import create_new_semester, setup


class SubdepartmentTestCase(TestCase):
    """Tests for Subdepartment model."""

    def setUp(self):
        setup(self)

    def test_subdepartment_name(self):
        """Test __str__ method in Subdepartment model"""
        self.assertEqual("CS - Computer Science", str(self.subdepartment))

    def test_recent_courses_has_recent_courses(self):
        """Test recent_courses method in Subdepartment model when there are recent courses"""
        recent_courses = Course.objects.filter(
            title__in=[self.course.title, self.course2.title]
        )

        self.assertQuerysetEqual(
            self.subdepartment.recent_courses(),
            recent_courses,
            transform=lambda x: x,  # Needed so that the formatting works
            ordered=False,
        )

    def test_recent_courses_has_no_recent_courses(self):
        """Test recent_courses method in Subdepartment model when there are not recent courses"""
        create_new_semester(self, 2050)
        self.assertFalse(self.subdepartment.recent_courses().exists())

    def test_has_current_course_true(self):
        """Test has_current_course method in
        Subdepartment model when it does have a course in the current semester
        """
        self.assertTrue(self.subdepartment.has_current_course())

    def test_has_current_course_false(self):
        """Test has_current_course method in Subdepartment model
        when it does not have a course in the current semester"""
        create_new_semester(self, 2050)
        self.assertFalse(self.subdepartment.has_current_course())
