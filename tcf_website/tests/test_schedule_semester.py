# pylint: disable=no-member
"""Tests for semester-scoped schedules."""

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Schedule, ScheduledCourse, Section
from .test_utils import setup


class ScheduleSemesterTestCase(TestCase):
    """Schedule builder filtered by term."""

    def setUp(self):
        setup(self)
        self.client = Client()
        self.client.force_login(self.user1)

    def test_view_schedules_filters_by_semester_query(self):
        """?semester= shows only schedules for that term."""
        Schedule.objects.create(
            name="Fall plan", user=self.user1, semester=self.semester
        )
        Schedule.objects.create(
            name="Old plan", user=self.user1, semester=self.past_semester
        )

        url = reverse("schedule")
        response = self.client.get(url, {"semester": self.past_semester.pk})
        self.assertEqual(response.status_code, 200)
        schedules = list(response.context["schedules"])
        self.assertEqual(len(schedules), 1)
        self.assertEqual(schedules[0].name, "Old plan")

        response_latest = self.client.get(url, {"semester": self.semester.pk})
        names = [s.name for s in response_latest.context["schedules"]]
        self.assertIn("Fall plan", names)
        self.assertNotIn("Old plan", names)

    def test_new_schedule_assigns_posted_semester(self):
        """POST semester creates a schedule in that term."""
        url = reverse("new_schedule")
        self.client.post(
            url,
            {
                "name": "Spring draft",
                "semester": str(self.past_semester.pk),
                "next": reverse("schedule"),
            },
        )
        created = Schedule.objects.get(name="Spring draft", user=self.user1)
        self.assertEqual(created.semester_id, self.past_semester.pk)

    def test_add_course_rejects_cross_semester_section(self):
        """Section from another term does not match the selected schedule."""
        schedule = Schedule.objects.create(
            name="Past", user=self.user1, semester=self.past_semester
        )
        Section.objects.create(
            course=self.course,
            semester=self.past_semester,
            sis_section_number=999,
        )
        section_current = Section.objects.create(
            course=self.course,
            semester=self.semester,
            sis_section_number=888,
        )
        section_current.instructors.set([self.instructor])

        post_url = reverse("schedule_add_course", args=[self.course.pk])
        response = self.client.post(
            post_url,
            {
                "schedule_id": str(schedule.pk),
                "selection": f"{section_current.pk}:{self.instructor.pk}",
                "semester": str(self.past_semester.pk),
                "next": reverse("schedule"),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            ScheduledCourse.objects.filter(
                schedule=schedule, section=section_current
            ).exists()
        )
