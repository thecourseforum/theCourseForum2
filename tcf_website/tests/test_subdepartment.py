# pylint: disable=no-member
"""Tests for Course model."""

from django.test import TestCase

from .test_utils import setup, create_new_sem


class SubdepartmentTestCase(TestCase):
    """Tests for Subdepartment model."""

    def setUp(self):
        setup(self)

    def test_subdepartment_name(self):
        """Test __str__ method in Subdepartment model"""
        self.assertEqual("CS - Computer Science", str(
            self.subdepartment))

    def test_recent_courses_has_recent_courses(self):
        """Test recent_courses method in Subdepartment model when there are recent courses"""
        self.assertEqual(
            "<QuerySet [<Course: CS 1420 | Software Testing>, <Course: CS 1421 | Algorithms>]>",
            str(self.subdepartment.recent_courses()))

    def test_recent_courses_has_no_recent_courses(self):
        """Test recent_courses method in Subdepartment model when there are not recent courses"""
        create_new_sem(self, 2050)
        self.assertEqual(
            "<QuerySet []>",
            str(self.subdepartment.recent_courses()))

    def test_has_current_course_true(self):
        """Test has_current_course method in
        Subdepartment model when it does have a course in the current semester"""
        self.assertTrue(self.subdepartment.has_current_course())

    def test_has_current_course_false(self):
        """Test has_current_course method in Subdepartment model
        when it does not have a course in the current semester"""
        create_new_sem(self, 2050)
        self.assertFalse(self.subdepartment.has_current_course())
