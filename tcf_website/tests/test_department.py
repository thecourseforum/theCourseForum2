# pylint: disable=no-member, line-too-long
"""Tests for Department model."""

from random import randint, sample, uniform

from django.test import TestCase

from ..models import Course, CourseGrade, Review, Semester
from .test_utils import create_new_semester, setup


class DepartmentTestCase(TestCase):
    """Tests for Department model."""

    def setUp(self):
        setup(self)
        Course.objects.all().delete()
        Review.objects.all().delete()
        self.courses = []
        self.latest_semester = Semester.latest()
        course_numbers = sample(range(1000, 4000), 50)
        for course_number in course_numbers:
            # Create random semester using helper method
            create_new_semester(
                self,
                randint(
                    self.latest_semester.year - 10, self.latest_semester.year
                ),
            )
            # Generate random courses
            course = Course.objects.create(
                title="Intro to Programming",
                subdepartment=self.subdepartment,
                semester_last_taught=self.semester,
                number=course_number,
            )
            self.courses.append(course)
            CourseGrade.objects.create(course=course, average=uniform(0, 4))
            for _ in range(5):
                Review.objects.create(
                    user=self.user1,
                    course=course,
                    semester=self.semester,
                    instructor=self.instructor,
                    text="Cool.",
                    instructor_rating=randint(1, 5),
                    difficulty=randint(1, 5),
                    recommendability=randint(1, 5),
                    enjoyability=randint(1, 5),
                    hours_per_week=randint(1, 5),
                    amount_group=randint(1, 5),
                    amount_reading=randint(1, 5),
                    amount_writing=randint(1, 5),
                    amount_homework=randint(1, 5),
                )

    def get_expected_courses(self, num_of_years: int = 5):
        """Helper method for fetching course objects in Department"""
        expected_courses = [
            course
            for course in self.courses
            if course.semester_last_taught.number
            >= self.latest_semester.number - (10 * num_of_years)
        ]

        return expected_courses

    def test_department_name(self):
        """Test Department model __str__ method"""
        self.assertEqual(str(self.department), "Computer Science")

    def test_fetch_recent_courses_last_five(self):
        """Test Department fetch recent courses function"""
        recent_courses = self.department.fetch_recent_courses()
        self.latest_semester = Semester.latest()
        expected_courses = self.get_expected_courses()
        self.assertEqual(set(recent_courses), set(expected_courses))

    def test_fetch_recent_courses_current_semester(self):
        """Test Department fetch recent courses function"""
        recent_courses = self.department.fetch_recent_courses(0)
        self.latest_semester = Semester.latest()
        expected_courses = self.get_expected_courses(0)
        self.assertEqual(set(recent_courses), set(expected_courses))

    def test_sort_courses_course_id_asc(self):
        """Test Department sort courses function using `Course ID` as the sort key (ascending)"""
        recent_courses = self.department.sort_courses("course_id")
        self.latest_semester = Semester.latest()
        expected_courses = self.get_expected_courses()
        expected_courses.sort(key=lambda x: x.number)
        self.assertEqual(list(recent_courses), expected_courses)

    def test_sort_courses_course_id_desc(self):
        """Test Department sort courses function using `Course` as the sort key (descending)"""
        recent_courses = self.department.sort_courses("course_id", 5, "desc")
        self.latest_semester = Semester.latest()
        expected_courses = self.get_expected_courses()
        expected_courses.sort(key=lambda x: -x.number)
        self.assertEqual(list(recent_courses), expected_courses)

    def test_sort_courses_gpa_asc(self):
        """Test Department sort courses function using 'gpa' as the sort key (ascending)"""
        self.latest_semester = Semester.latest()
        recent_courses = self.department.sort_courses("gpa")
        expected_courses = self.get_expected_courses()
        expected_courses.sort(
            key=lambda x: (
                round(x.average_gpa(), 10),
                x.subdepartment.name,
                x.number,
            )
        )
        self.assertEqual(list(recent_courses), expected_courses)

    def test_sort_courses_gpa_desc(self):
        """Test Department sort courses function using 'gpa' as the sort key (descending)"""
        self.latest_semester = Semester.latest()
        recent_courses = self.department.sort_courses("gpa", 5, "desc")
        expected_courses = self.get_expected_courses()
        expected_courses.sort(
            key=lambda x: (
                -round(x.average_gpa(), 10),
                x.subdepartment.name,
                x.number,
            )
        )
        self.assertEqual(list(recent_courses), expected_courses)

    def test_sort_courses_rating_asc(self):
        """Test Department sort courses function using 'rating' as the sort key (ascending)"""
        self.latest_semester = Semester.latest()
        recent_courses = self.department.sort_courses("rating")
        expected_courses = self.get_expected_courses()
        expected_courses.sort(
            key=lambda x: (
                round(x.average_rating(), 10),
                x.subdepartment.name,
                x.number,
            )
        )
        self.assertEqual(list(recent_courses), expected_courses)

    def test_sort_courses_rating_desc(self):
        """Test Department sort courses function using 'rating' as the sort key (descending)"""
        self.latest_semester = Semester.latest()
        recent_courses = self.department.sort_courses("rating", 5, "desc")
        expected_courses = self.get_expected_courses()
        expected_courses.sort(
            key=lambda x: (
                -round(x.average_rating(), 10),
                x.subdepartment.name,
                x.number,
            )
        )
        self.assertEqual(list(recent_courses), expected_courses)

    def test_sort_courses_difficulty_asc(self):
        """Test Department sort courses function using 'difficulty' as the sort key (ascending)"""
        self.latest_semester = Semester.latest()
        recent_courses = self.department.sort_courses("difficulty")
        expected_courses = self.get_expected_courses()
        expected_courses.sort(
            key=lambda x: (
                round(x.average_difficulty(), 10),
                x.subdepartment.name,
                x.number,
            )
        )
        self.assertEqual(list(recent_courses), expected_courses)

    def test_sort_courses_difficulty_desc(self):
        """Test Department sort courses function using 'difficulty' as the sort key (descending)"""
        self.latest_semester = Semester.latest()
        recent_courses = self.department.sort_courses("difficulty", 5, "desc")
        expected_courses = self.get_expected_courses()
        expected_courses.sort(
            key=lambda x: (
                -round(x.average_difficulty(), 10),
                x.subdepartment.name,
                x.number,
            )
        )
        self.assertEqual(list(recent_courses), expected_courses)
