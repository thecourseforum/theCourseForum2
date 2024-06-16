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
        self.latest_semester = Semester().latest()
        course_numbers = set()
        for _ in range(50):
            # Create random semester using helper method
            create_new_semester(
                self,
                randint(
                    self.latest_semester.year - 10, self.latest_semester.year
                ),
            )
            # Generate random course numbers
            while True:
                course_number = randint(1000, 2000)
                if course_number not in course_numbers:
                    course_numbers.add(course_number)
                    break

            # Generate random courses
            course = Course.objects.create(
                title="Intro to Programming",
                subdepartment=self.subdepartment,
                semester_last_taught=self.semester,
                number=course_number,
            )
            self.courses.append(course)

    def test_department_name(self):
        """Test Department model __str__ method"""
        self.assertEqual(str(self.department), "Computer Science")

    def test_fetch_recent_courses_last_five(self):
        """Test Department fetch recent courses function"""
        recent_courses = self.department.fetch_recent_courses()

        expected_courses = [
            course
            for course in self.courses
            if course.semester_last_taught.number
            >= self.latest_semester.number - 50
        ]

    def test_fetch_recent_courses_current_semester(self):
        """Test Department fetch recent courses function"""
        recent_courses = self.department.fetch_recent_courses(0)
        expected_courses = [
            course
            for course in self.courses
            if course.semester_last_taught.number > self.latest_semester.number
        ]
        self.assertEqual(set(recent_courses), set(expected_courses))
