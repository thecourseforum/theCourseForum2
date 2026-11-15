"""Tests for the per-semester filter on the course-instructor page."""

import json

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import reverse

from ..models import (
    Course,
    CourseInstructorGrade,
    CourseInstructorSemesterGrade,
    Department,
    Instructor,
    Review,
    School,
    Section,
    Semester,
    Subdepartment,
    User,
)


class CourseInstructorSemesterFilterTestCase(TestCase):
    """The ?semester= filter on the course-instructor page."""

    @classmethod
    def setUpTestData(cls):
        school = School.objects.create(name="Engineering")
        department = Department.objects.create(name="Computer Science", school=school)
        subdepartment = Subdepartment.objects.create(
            name="Computer Science", mnemonic="CS", department=department
        )

        cls.fall = Semester.objects.create(year=2025, season="FALL", number=1258)
        cls.spring = Semester.objects.create(year=2025, season="SPRING", number=1252)
        # Only has a hidden review, so it should not appear in the dropdown.
        cls.hidden_only = Semester.objects.create(year=2024, season="FALL", number=1248)

        cls.course = Course.objects.create(
            title="Software Testing",
            description="Tests.",
            number=3240,
            subdepartment=subdepartment,
            semester_last_taught=cls.fall,
        )
        cls.instructor = Instructor.objects.create(
            first_name="Ada", last_name="Lovelace"
        )
        section = Section.objects.create(
            course=cls.course, semester=cls.fall, sis_section_number=10001
        )
        section.instructors.add(cls.instructor)

        # All-time grades vs. Fall-only grades (Spring has reviews but no grades).
        CourseInstructorGrade.objects.create(
            course=cls.course, instructor=cls.instructor, average=3.0, a=10
        )
        CourseInstructorSemesterGrade.objects.create(
            course=cls.course,
            instructor=cls.instructor,
            semester=cls.fall,
            average=3.5,
            a=7,
            total_enrolled=7,
        )

        cls.user = User.objects.create(username="tester", computing_id="tst1a")
        cls.fall_review = cls._review(cls.fall, "Great class.", rating=5)
        cls.spring_review = cls._review(cls.spring, "Rough class.", rating=1)
        cls._review(cls.hidden_only, "Hidden review.", rating=3, hidden=True)

        cls.url = reverse("course_instructor", args=[cls.course.id, cls.instructor.id])

    @classmethod
    def _review(cls, semester, text, rating, hidden=False):
        return Review.objects.create(
            user=cls.user,
            course=cls.course,
            instructor=cls.instructor,
            semester=semester,
            text=text,
            instructor_rating=rating,
            difficulty=3,
            recommendability=rating,
            enjoyability=rating,
            hours_per_week=5,
            amount_reading=1,
            amount_writing=1,
            amount_group=1,
            amount_homework=2,
            hidden=hidden,
        )

    def _get(self, params=None):
        response = self.client.get(self.url, params or {})
        self.assertEqual(response.status_code, 200)
        return response, json.loads(response.context["data"])

    def test_no_semester_shows_all_time(self):
        """Without ?semester=, grades, ratings and reviews cover every semester."""
        response, data = self._get()
        self.assertIsNone(response.context["selected_semester"])
        self.assertEqual(data["average_gpa"], 3.0)
        self.assertEqual(data["instructor"], 3.0)
        self.assertEqual(response.context["num_reviews"], 2)
        self.assertEqual(len(response.context["paginated_reviews"]), 2)

    def test_semester_filters_grades_ratings_and_reviews(self):
        """With ?semester=, every part of the page covers only that semester."""
        response, data = self._get({"semester": self.fall.number})
        self.assertEqual(response.context["selected_semester"], self.fall)
        self.assertEqual(data["average_gpa"], 3.5)
        self.assertEqual(data["a"], 7)
        self.assertEqual(data["instructor"], 5.0)
        self.assertEqual(response.context["num_reviews"], 1)
        self.assertEqual(
            list(response.context["paginated_reviews"]), [self.fall_review]
        )

    def test_semester_without_grade_data(self):
        """A semester with reviews but no grade row shows ratings and no grades."""
        response, data = self._get({"semester": self.spring.number})
        self.assertNotIn("average_gpa", data)
        self.assertEqual(data["instructor"], 1.0)
        self.assertEqual(
            list(response.context["paginated_reviews"]), [self.spring_review]
        )

    def test_invalid_semester_falls_back_to_all_time(self):
        """Junk or unknown semester numbers show the all-time page."""
        for value in ("abc", "9999", ""):
            with self.subTest(semester=value):
                response, data = self._get({"semester": value})
                self.assertIsNone(response.context["selected_semester"])
                self.assertEqual(data["average_gpa"], 3.0)
                self.assertEqual(response.context["num_reviews"], 2)

    def test_semester_options(self):
        """Dropdown lists semesters with grades or visible reviews, newest first."""
        response, _ = self._get()
        self.assertEqual(
            list(response.context["semester_options"]), [self.fall, self.spring]
        )
        self.assertContains(response, 'id="semester-select"')

    def test_get_sorted_reviews_filters_by_semester(self):
        """Review.get_sorted_reviews returns only the given semester's reviews."""
        reviews = Review.get_sorted_reviews(
            self.course.id, self.instructor.id, AnonymousUser(), semester=self.fall
        )
        self.assertEqual(list(reviews), [self.fall_review])

    def test_get_sorted_reviews_without_semester(self):
        """With no semester, Review.get_sorted_reviews returns every visible review."""
        reviews = Review.get_sorted_reviews(
            self.course.id, self.instructor.id, AnonymousUser()
        )
        self.assertCountEqual(list(reviews), [self.fall_review, self.spring_review])
