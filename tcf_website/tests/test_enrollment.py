"""Tests for enrollment data updates."""
from unittest.mock import patch
from django.test import TestCase
from tcf_website.models import (
    Course, Department, School, Section,
    SectionEnrollment, Semester, Subdepartment
)
from tcf_website.api.enrollment import update_enrollment_data


class TestEnrollment(TestCase):
    """Test cases for enrollment data updates."""

    def setUp(self):
        """Set up test data."""
        self.school = School.objects.create(name="Test School")
        self.department = Department.objects.create(
            name="Test Department",
            school=self.school
        )
        self.subdepartment = Subdepartment.objects.create(
            name="Test Subdepartment",
            department=self.department
        )
        self.semester = Semester.objects.create(
            number="1234",
            year=2025
        )
        self.course = Course.objects.create(
            title="Test Course",
            number=101,
            subdepartment=self.subdepartment,
            semester_last_taught=self.semester
        )
        self.section = Section.objects.create(
            course=self.course,
            semester=self.semester,
            sis_section_number="99999"
        )
        self.enrollment = SectionEnrollment.objects.create(
            section=self.section,
            enrollment_taken=10,
            enrollment_limit=20,
            waitlist_taken=5,
            waitlist_limit=10
        )

    @patch("tcf_website.api.enrollment.fetch_section_data")
    def test_mocked_update_enrollment_data(self, mock_fetch):
        """Test enrollment data update with mocked data."""
        mock_fetch.return_value = {
            "enrollment_taken": 10,
            "enrollment_limit": 20,
            "waitlist_taken": 5,
            "waitlist_limit": 10,
        }
        update_enrollment_data(self.course.id)
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.enrollment_taken, 10)
        self.assertEqual(self.enrollment.enrollment_limit, 20)
        self.assertEqual(self.enrollment.waitlist_taken, 5)
        self.assertEqual(self.enrollment.waitlist_limit, 10)

    def test_update_enrollment_data(self):
        """Test enrollment data update with real data."""
        update_enrollment_data(self.course.id)
        self.enrollment.refresh_from_db()
        self.assertGreaterEqual(self.enrollment.enrollment_taken, 0)
        self.assertGreaterEqual(self.enrollment.enrollment_limit, 0)
