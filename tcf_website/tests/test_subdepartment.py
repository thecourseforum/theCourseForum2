# pylint: disable=no-member
"""Tests for Course model."""

from django.test import TestCase

from .test_utils import setup, create_new_semester
from ..models import Course


class SubjectTestCase(TestCase):
    """Tests for Subject model."""

    def setUp(self):
        setup(self)

    def test_subject_name(self):
        """Test __str__ method in Subject model"""
        self.assertEqual("CS - Computer Science", str(self.subject))

    def test_recent_courses_has_recent_courses(self):
        """Test recent_courses method in Subject model when there are recent courses"""
        recent_courses = Course.objects.filter(title__in=[self.course.title, self.course2.title])

        self.assertQuerysetEqual(
            self.subject.recent_courses(),
            recent_courses,
            transform=lambda x: x,  # Needed so that the formatting works
            ordered=False)

    def test_recent_courses_has_no_recent_courses(self):
        """Test recent_courses method in Subject model when there are not recent courses"""
        create_new_semester(self, 2050)
        self.assertFalse(self.subject.recent_courses().exists())

    def test_has_current_course_true(self):
        """Test has_current_course method in
        Subject model when it does have a course in the current semester"""
        self.assertTrue(self.subject.has_current_course())

    def test_has_current_course_false(self):
        """Test has_current_course method in Subject model
        when it does not have a course in the current semester"""
        create_new_semester(self, 2050)
        self.assertFalse(self.subject.has_current_course())
