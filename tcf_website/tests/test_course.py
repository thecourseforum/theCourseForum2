"""Tests for Course model."""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..models import Instructor, Section, Semester
from .test_utils import setup


class CourseTestCase(TestCase):
    """Tests for course model."""

    def setUp(self):
        setup(self)

    def test_review_count(self):
        """Test review count method"""
        self.assertEqual(self.course.review_count(), 2)

    def test_code(self):
        """Course code string."""
        code = self.course.code()
        self.assertEqual(code, "CS 1420")

    def test_is_recent(self):
        """Test for is_recent()."""
        self.assertTrue(self.course.is_recent())

        Semester.objects.create(year=2026, season="JANUARY", number=1261)

        self.assertFalse(self.course.is_recent())

    def test_average_rating(self):
        """Test average rating."""
        rating = (self.review1.average() + self.review2.average()) / 2

        self.assertAlmostEqual(self.course.average_rating(), rating, 4)

    def test_average_difficulty(self):
        """Test average difficulty."""
        difficulty = (self.review1.difficulty + self.review2.difficulty) / 2

        self.assertAlmostEqual(self.course.average_difficulty(), difficulty, 4)

    def test_average_rating_no_reviews(self):
        """Test average rating no reviews."""
        self.review1.delete()
        self.review2.delete()

        self.assertIsNone(self.course.average_rating())

    def test_average_difficulty_no_reviews(self):
        """Test average difficulty no reviews."""
        self.review1.delete()
        self.review2.delete()

        self.assertIsNone(self.course.average_difficulty())

    def test_student_eval_link(self):
        """Test if a student eval link matches up with a real link."""
        eval_link = (
            "https://evals.itc.virginia.edu/"
            + "course-selectionguide/pages/SGMain.jsp?cmp=CS,1420"
        )
        # split across lines for readability (line length)
        # this link doesn't actually work because CS 420 is not a real class
        self.assertEqual(eval_link, self.course.eval_link())


class CourseInstructorOrderTestCase(TestCase):
    """Tests for how the course page orders instructors by semester last taught."""

    def setUp(self):
        setup(self)
        year = timezone.now().year
        self.fall = Semester.objects.get_or_create(
            year=year, season="FALL", defaults={"number": int(f"1{year % 100}8")}
        )[0]
        self.summer = Semester.objects.get_or_create(
            year=year, season="SUMMER", defaults={"number": int(f"1{year % 100}6")}
        )[0]
        self.assertLess(self.fall.pk, self.summer.pk)

        self.fall_instructor = Instructor.objects.create(
            first_name="Fall", last_name="Teacher"
        )
        self.summer_instructor = Instructor.objects.create(
            first_name="Summer", last_name="Teacher"
        )
        for instructor, semester in (
            (self.fall_instructor, self.fall),
            (self.summer_instructor, self.summer),
        ):
            section = Section.objects.create(
                course=self.course,
                semester=semester,
                sis_section_number=10000 + semester.number,
            )
            section.instructors.set([instructor])

    def sorted_instructors(self, order):
        """Instructors for the last-5-years view, sorted by semester last taught."""
        return list(
            self.course.sort_instructors_by_key(
                Semester.latest(), False, order, "last_taught"
            )
        )

    def test_recent_semester_sorts_first_regardless_of_load_order(self):
        """Fall outranks Summer of the same year even though it was loaded first."""
        instructors = self.sorted_instructors("desc")

        self.assertEqual(
            [self.fall_instructor.pk, self.summer_instructor.pk],
            [i.pk for i in instructors[:2]],
        )

    def test_ascending_order_puts_oldest_semester_first(self):
        """Ascending order is the exact reverse ranking by semester."""
        instructors = self.sorted_instructors("asc")
        order = [i.pk for i in instructors]

        self.assertLess(
            order.index(self.summer_instructor.pk),
            order.index(self.fall_instructor.pk),
        )

    def test_semester_last_taught_number_is_the_sis_semester_code(self):
        """The course view resolves this annotation back into a Semester."""
        instructors = {i.pk: i for i in self.sorted_instructors("desc")}

        self.assertEqual(
            self.fall.number,
            instructors[self.fall_instructor.pk].semester_last_taught_number,
        )
        self.assertEqual(
            self.summer.number,
            instructors[self.summer_instructor.pk].semester_last_taught_number,
        )

    def test_course_page_labels_each_instructor_with_their_last_semester(self):
        """The rendered page resolves semester numbers into display names."""
        url = reverse("course", args=["CS", self.course.number])
        response = self.client.get(url, {"latest": "false"})
        rendered = response.content.decode()

        self.assertEqual(200, response.status_code)
        self.assertLess(
            rendered.index(str(self.fall)),
            rendered.index(str(self.summer)),
            "Fall should be rendered above Summer",
        )
        self.assertNotIn("Unknown", rendered)
