"""Tests for Django management commands"""

from django.core import management
from django.test import TestCase

from tcf_website.models import CourseGrade, CourseInstructorGrade

from .test_utils import setup


class LoadGradesTestCase(TestCase):
    """Tests for the load_grades command. Uses the test_data.csv file, which holds dummy
    data for two sections of the same course taught by the same instructor."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)
        # Clearing is required to pass tests
        CourseGrade.objects.all().delete()
        CourseInstructorGrade.objects.all().delete()
        management.call_command(
            "load_grades", "test/test_data", "--suppress-tqdm", verbosity=0
        )
        cls.cg = CourseGrade.objects.first()
        cls.cig = CourseInstructorGrade.objects.first()

    def test_no_duplicates(self):
        """Make sure only one instance of CourseGrade and CourseInstructorGrade were created.
        In particular, make sure that the blank row does *not* have an object created for it.
        """
        self.assertEqual(CourseGrade.objects.count(), 1)
        self.assertEqual(CourseInstructorGrade.objects.count(), 1)

    def test_correct_course(self):
        """Make sure the course for both is CS 1420"""
        self.assertEqual(self.cg.course, self.cig.course)

    def test_correct_instructor(self):
        """Make sure instructor is Tom Jefferson"""
        self.assertEqual(self.cig.instructor.full_name(), "Tom Jefferson")

    def test_total_students(self):
        """Check valid total_enrolled"""
        self.assertEqual(self.cg.total_enrolled, 24)
        self.assertEqual(self.cig.total_enrolled, 24)

    def test_correct_distribution(self):
        """Make sure both instances match expected values"""
        self.assert_correct_data(self.cg)
        self.assert_correct_data(self.cig)

    def assert_correct_data(self, model):
        """Helper function. Checks model's data against expected values from
        manually adding together the two rows in the CSV."""
        self.assertEqual(model.a_plus, 1)
        self.assertEqual(model.a, 4)
        self.assertEqual(model.a_minus, 6)
        self.assertEqual(model.b_plus, 3)
        self.assertEqual(model.b, 0)
        self.assertEqual(model.b_minus, 3)
        self.assertEqual(model.c_plus, 1)
        self.assertEqual(model.c, 2)
        self.assertEqual(model.c_minus, 0)
        self.assertEqual(model.dfw, 4)

    def test_matching_data(self):
        """Make sure both instances match each other"""
        # pylint: disable=duplicate-code
        for field in [
            "a_plus",
            "a",
            "a_minus",
            "b_plus",
            "b",
            "b_minus",
            "c_plus",
            "c",
            "c_minus",
            "dfw",
        ]:
            cg_field = getattr(self.cg, field)
            cig_field = getattr(self.cig, field)
            self.assertEqual(cg_field, cig_field)


class LoadGradesMissingAggregate(TestCase):
    """Tests case when aggregate data (Course GPA/# Students) is not provided."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)
        CourseGrade.objects.all().delete()
        CourseInstructorGrade.objects.all().delete()
        management.call_command(
            "load_grades",
            "test/missing_aggregate",
            "--suppress-tqdm",
            verbosity=0,
        )
        cls.cg = CourseGrade.objects.first()
        cls.cig = CourseInstructorGrade.objects.first()

    def test_total_students(self):
        """Check valid total_enrolled even when not provided"""
        self.assertEqual(self.cg.total_enrolled, 10)
        self.assertEqual(self.cig.total_enrolled, 10)


class LoadGradesMissingDistribution(TestCase):
    """Tests case when distribution data is not provided."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)
        CourseGrade.objects.all().delete()
        CourseInstructorGrade.objects.all().delete()
        management.call_command(
            "load_grades",
            "test/missing_distribution",
            "--suppress-tqdm",
            verbosity=0,
        )
        cls.cg = CourseGrade.objects.first()
        cls.cig = CourseInstructorGrade.objects.first()

    def test_aggregate_stats(self):
        """Check aggregate stats across sections combined correctly"""
        self.assertEqual(self.cg.average, 3)
        self.assertEqual(self.cig.average, 3)

        self.assertEqual(self.cg.total_enrolled, 4)
        self.assertEqual(self.cig.total_enrolled, 4)
