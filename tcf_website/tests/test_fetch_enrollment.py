"""Tests for fetch_enrollment management command."""

from unittest.mock import patch
from django.test import TestCase
from tcf_website.models import (
    Course, Department, School, Section,
    SectionEnrollment, Semester, Subdepartment
)
from tcf_website.management.commands.fetch_enrollment import fetch_section_data


class FetchEnrollmentTestCase(TestCase):
    """Tests for the fetch_enrollment command."""

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

    @patch('tcf_website.management.commands.fetch_enrollment.session.get')
    def test_fetch_enrollment_success(self, mock_get):
        """Test successful enrollment fetch."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "classes": [{
                "enrollment_total": 15,
                "class_capacity": 20,
                "wait_tot": 5,
                "wait_cap": 10
            }]
        }

        fetch_section_data(self.section)

        enrollment = SectionEnrollment.objects.get(section=self.section)
        self.assertEqual(enrollment.enrollment_taken, 15)
        self.assertEqual(enrollment.enrollment_limit, 20)
        self.assertEqual(enrollment.waitlist_taken, 5)
        self.assertEqual(enrollment.waitlist_limit, 10)

    @patch('tcf_website.management.commands.fetch_enrollment.session.get')
    def test_fetch_enrollment_update_existing(self, mock_get):
        """Test updating existing enrollment data."""
        # Create initial enrollment
        SectionEnrollment.objects.create(
            section=self.section,
            enrollment_taken=10,
            enrollment_limit=20,
            waitlist_taken=2,
            waitlist_limit=5
        )

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "classes": [{
                "enrollment_total": 15,
                "class_capacity": 25,
                "wait_tot": 8,
                "wait_cap": 12
            }]
        }

        fetch_section_data(self.section)

        enrollment = SectionEnrollment.objects.get(section=self.section)
        self.assertEqual(enrollment.enrollment_taken, 15)
        self.assertEqual(enrollment.enrollment_limit, 25)
        self.assertEqual(enrollment.waitlist_taken, 8)
        self.assertEqual(enrollment.waitlist_limit, 12)

    @patch('tcf_website.management.commands.fetch_enrollment.session.get')
    def test_fetch_enrollment_empty_response(self, mock_get):
        """Test handling of empty API response."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"classes": []}

        result = fetch_section_data(self.section)

        self.assertFalse(result)
        self.assertEqual(SectionEnrollment.objects.count(), 0)

    @patch('tcf_website.management.commands.fetch_enrollment.session.get')
    def test_fetch_enrollment_api_error(self, mock_get):
        """Test handling of API error."""
        mock_get.return_value.status_code = 500
        mock_get.return_value.raise_for_status.side_effect = Exception("API Error")

        result = fetch_section_data(self.section)

        self.assertFalse(result)
        self.assertEqual(SectionEnrollment.objects.count(), 0)
