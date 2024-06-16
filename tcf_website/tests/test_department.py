# pylint: disable=no-member
"""Tests for Department model."""

from random import choice, randint
from unittest.mock import MagicMock

from django.test import TestCase

from ..models import Course, Semester
from .test_utils import create_new_semester, setup


class DepartmentTestCase(TestCase):
    """Tests for Department model."""

    def setUp(self):
        setup(self)
        Course.objects.all().delete()
        self.courses = []
        for _ in range(5):
            create_new_semester(
                self,
                randint(
                    Semester().latest().year - 10, Semester().latest().year
                ),
            )
            course = Course.objects.create(
                title=f"Course {randint(1, 100)}",
                subdepartment=self.subdepartment,
                semester_last_taught=self.semester,
                number=randint(1000, 2000),
            )
            self.courses.append(course)

    def test_department_name(self):
        """Test Department model __str__ method"""
        self.assertEqual(str(self.department), "Computer Science")

    def test_fetch_recent_courses(self):
        """Test Department fetch recent courses function"""
        latest_semester = Semester().latest()
        recent_courses = self.department.fetch_recent_courses()

        expected_courses = [
            course
            for course in self.courses
            if course.semester_last_taught.number >= latest_semester.number - 50
        ]

        self.assertEqual(set(recent_courses), set(expected_courses))
