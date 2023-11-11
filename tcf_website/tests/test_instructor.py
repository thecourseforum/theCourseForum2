# pylint: disable=no-member
"""Tests for Instructor model."""

from django.test import TestCase
from django.urls import reverse

from ..models import Section
from ..views.browse import safe_round
from .test_utils import setup


class InstructorTestCase(TestCase):
    """Tests for instructor model."""

    def setUp(self):
        setup(self)

    def test_full_name(self):
        """Course full name string."""
        self.assertEqual(self.instructor.full_name(), "Tom Jefferson")

    def test_average_rating_for_course(self):
        """Test average rating for an instructor's particular course."""
        rating = (
            self.review1.recommendability
            + self.review2.recommendability
            + self.review1.instructor_rating
            + self.review2.instructor_rating
            + self.review1.enjoyability
            + self.review2.enjoyability
        ) / 6

        self.assertAlmostEqual(
            self.instructor.average_rating_for_course(self.course), rating, 4
        )

    def test_average_difficulty_for_course(self):
        """Test average difficulty for a particular course."""
        difficulty = (self.review1.difficulty + self.review2.difficulty) / 2

        self.assertAlmostEqual(
            self.instructor.average_difficulty_for_course(self.course),
            difficulty,
            4,
        )

    def test_average_enjoyability_for_course(self):
        """Test average enjoyability for a particular course."""
        enjoyability = (
            self.review1.enjoyability + self.review2.enjoyability
        ) / 2

        self.assertAlmostEqual(
            self.instructor.average_enjoyability_for_course(self.course),
            enjoyability,
            4,
        )

    def test_average_instructor_rating_for_course(self):
        """Test average instructor rating for a particular course."""
        instructor_rating = (
            self.review1.instructor_rating + self.review2.instructor_rating
        ) / 2

        self.assertAlmostEqual(
            self.instructor.average_instructor_rating_for_course(self.course),
            instructor_rating,
            4,
        )

    def test_average_recommendability_for_course(self):
        """Test average recommendability for a particular course."""
        average_recommendability = (
            self.review1.recommendability + self.review2.recommendability
        ) / 2

        self.assertAlmostEqual(
            self.instructor.average_recommendability_for_course(self.course),
            average_recommendability,
            4,
        )

    def test_average_hours_for_course(self):
        """Test average hours for a particular course."""
        average_hours = (
            self.review1.hours_per_week + self.review2.hours_per_week
        ) / 2

        self.assertAlmostEqual(
            self.instructor.average_hours_for_course(self.course),
            average_hours,
            4,
        )

    def test_average_reading_hours_for_course(self):
        """Test average reading hours for a particular course."""
        average_reading = (
            self.review1.amount_reading + self.review2.amount_reading
        ) / 2

        self.assertAlmostEqual(
            self.instructor.average_reading_hours_for_course(self.course),
            average_reading,
            4,
        )

    def test_average_writing_hours_for_course(self):
        """Test average writing hours for a particular course."""
        average_writing = (
            self.review1.amount_writing + self.review2.amount_writing
        ) / 2

        self.assertAlmostEqual(
            self.instructor.average_writing_hours_for_course(self.course),
            average_writing,
            4,
        )

    def test_average_group_hours_for_course(self):
        """Test average group hours for a particular course."""
        average_group = (
            self.review1.amount_group + self.review2.amount_group
        ) / 2

        self.assertAlmostEqual(
            self.instructor.average_group_hours_for_course(self.course),
            average_group,
            4,
        )

    def test_average_other_hours_for_course(self):
        """Test average other hours for a particular course."""
        average_other = (
            self.review1.amount_homework + self.review2.amount_homework
        ) / 2

        self.assertAlmostEqual(
            self.instructor.average_other_hours_for_course(self.course),
            average_other,
            4,
        )

    def test_average_gpa_for_course(self):
        """Test average gpa for a particular course."""
        average_gpa_course = (
            self.instructor_grade.average + self.instructor_grade2.average
        ) / 2

        self.assertAlmostEqual(
            self.instructor.average_gpa_for_course(self.course),
            average_gpa_course,
            4,
        )

    def test_taught_courses(self):
        """Test taught courses for a particular section."""
        courses_taught = Section.objects.filter(
            course__in=[self.course, self.course2]
        )

        self.assertQuerysetEqual(
            self.instructor.taught_courses(),
            courses_taught,
            transform=lambda x: x,  # Needed so that the formatting works
            ordered=False,
        )

    def test_average_rating(self):
        """Test average rating for all of the courses taught by a specific instructor"""
        avg_recommendability = (
            self.review1.recommendability
            + self.review2.recommendability
            + self.review3.recommendability
            + self.review4.recommendability
            + self.review5.recommendability
            + self.review6.recommendability
        ) / 6

        avg_instructor_rating = (
            self.review1.instructor_rating
            + self.review2.instructor_rating
            + self.review3.instructor_rating
            + self.review4.instructor_rating
            + self.review5.instructor_rating
            + self.review6.instructor_rating
        ) / 6

        avg_enjoyability = (
            self.review1.enjoyability
            + self.review2.enjoyability
            + self.review3.enjoyability
            + self.review4.enjoyability
            + self.review5.enjoyability
            + self.review6.enjoyability
        ) / 6

        avg_rating = (
            avg_instructor_rating + avg_recommendability + avg_enjoyability
        ) / 3

        self.assertAlmostEqual(self.instructor.average_rating(), avg_rating, 4)

    def test_average_difficulty(self):
        """Test average difficulty for all of the courses taught by a specific instructor"""
        avg_difficulty = (
            self.review1.difficulty
            + self.review2.difficulty
            + self.review3.difficulty
            + self.review4.difficulty
            + self.review5.difficulty
            + self.review6.difficulty
        ) / 6

        self.assertEqual(self.instructor.average_difficulty(), avg_difficulty)

    def test_average_gpa(self):
        """Test average gpa for all of the courses taught by a specific instructor"""
        avg_gpa = (
            self.instructor_grade.average
            + self.instructor_grade2.average
            + self.instructor_grade3.average
        ) / 3
        self.assertEqual(self.instructor.average_gpa(), avg_gpa)

    def test_instructor_name(self):
        """Test __str__ method in Instructor model when there is an email"""
        self.assertEqual(
            "Tom Jefferson (tjt3rea@virginia.edu)", str(self.instructor)
        )

    def test_instructor_view(self):
        """Test if context variables are correct in the instructor view."""
        response = self.client.post(
            reverse("instructor", args=(self.instructor.id,))
        )
        difficulty = safe_round(self.instructor.average_difficulty())
        rating = safe_round(self.instructor.average_rating())
        self.assertEqual(difficulty, response.context[0]["avg_difficulty"])
        self.assertEqual(rating, response.context[0]["avg_rating"])
