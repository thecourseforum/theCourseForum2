"""Tests for Django management commands"""
from django.core import management
from django.test import TestCase

from tcf_website.models import CourseGrade, CourseInstructorGrade
from .test_utils import setup


class LoadGradesTestCase(TestCase):
    """ Tests for the load_grades command. Uses the test_data.csv file, which holds dummy
    data for two sections of the same course taught by the same instructor."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)
        management.call_command('load_grades', 'test_data', '--suppress-tqdm', verbosity=0)
        cls.cg = CourseGrade.objects.all()[0]
        cls.cig = CourseInstructorGrade.objects.all()[0]

    def test_no_duplicates(self):
        """Make sure only one instance of CourseGrade and CourseInstructorGrade were created"""
        self.assertEqual(len(CourseGrade.objects.all()), 1)
        self.assertEqual(len(CourseInstructorGrade.objects.all()), 1)

    def test_correct_course(self):
        """Make sure the course for both is CS 420"""
        self.assertEqual(self.cg.course, self.cig.course)

    def test_correct_instructor(self):
        """Make sure instructor is Tom Jefferson"""
        self.assertEqual(self.cig.instructor.full_name(), "Tom Jefferson")

    def test_total_students(self):
        """Check valid total_enrolled"""
        self.assertEqual(self.cg.total_enrolled, self.cig.total_enrolled)
        self.assertEqual(self.cg.total_enrolled, 24)

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
        self.assertEqual(model.not_pass, 4)

    def test_matching_data(self):
        """Make sure both instances match each other"""
        self.assertEqual(self.cig.a_plus, self.cig.a_plus)
        self.assertEqual(self.cg.a, self.cig.a)
        self.assertEqual(self.cg.a_minus, self.cig.a_minus)
        self.assertEqual(self.cg.b_plus, self.cig.b_plus)
        self.assertEqual(self.cg.b, self.cig.b)
        self.assertEqual(self.cg.b_minus, self.cig.b_minus)
        self.assertEqual(self.cg.c_plus, self.cig.c_plus)
        self.assertEqual(self.cg.c, self.cig.c)
        self.assertEqual(self.cg.c_minus, self.cig.c_minus)
        self.assertEqual(self.cg.not_pass, self.cig.not_pass)
