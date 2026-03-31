# pylint: disable=no-member
"""Tests for semester-scoped schedules."""

from django.test import Client, TestCase
from django.urls import reverse

from ..models import CourseInstructorGrade, Schedule, ScheduledCourse, Section
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
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            ScheduledCourse.objects.filter(
                schedule=schedule, section=section_current
            ).exists()
        )

    def test_schedule_add_course_cancel_link_uses_next(self):
        """Cancel returns to the originating page when next is provided."""
        Schedule.objects.create(name="Current", user=self.user1, semester=self.semester)
        response = self.client.get(
            reverse("schedule_add_course", args=[self.course.pk]),
            {
                "next": reverse(
                    "course_instructor", args=[self.course.pk, self.instructor.pk]
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'href="{reverse("course_instructor", args=[self.course.pk, self.instructor.pk])}"',
        )

    def test_course_instructor_page_links_to_schedule_add(self):
        """Instructor page add button uses the same schedule-add entry point."""
        CourseInstructorGrade.objects.filter(
            course=self.course,
            instructor=self.instructor,
        ).exclude(pk=self.instructor_grade.pk).delete()

        response = self.client.get(
            reverse("course_instructor", args=[self.course.pk, self.instructor.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'{reverse("schedule_add_course", args=[self.course.pk])}?next=',
        )

    def test_add_course_allows_multiple_selected_sections(self):
        """Posting multiple selections adds one scheduled row per checked section."""
        schedule = Schedule.objects.create(
            name="Current", user=self.user1, semester=self.semester
        )
        lecture_section = Section.objects.create(
            course=self.course,
            semester=self.semester,
            sis_section_number=101,
        )
        discussion_section = Section.objects.create(
            course=self.course,
            semester=self.semester,
            sis_section_number=102,
            section_type="LAB",
        )
        lecture_section.instructors.set([self.instructor])
        discussion_section.instructors.set([self.instructor])

        post_url = reverse("schedule_add_course", args=[self.course.pk])
        response = self.client.post(
            post_url,
            {
                "schedule_id": str(schedule.pk),
                "selection": [
                    f"{lecture_section.pk}:{self.instructor.pk}",
                    f"{discussion_section.pk}:{self.instructor.pk}",
                ],
                "semester": str(self.semester.pk),
                "next": reverse("schedule"),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            ScheduledCourse.objects.filter(schedule=schedule).count(),
            2,
        )

    def test_add_course_does_not_partially_add_multiple_selected_sections(self):
        """If one selected section fails, none of the new selections are added."""
        schedule = Schedule.objects.create(
            name="Current", user=self.user1, semester=self.semester
        )
        existing_section = Section.objects.create(
            course=self.course,
            semester=self.semester,
            sis_section_number=100,
        )
        lecture_section = Section.objects.create(
            course=self.course,
            semester=self.semester,
            sis_section_number=101,
        )
        discussion_section = Section.objects.create(
            course=self.course,
            semester=self.semester,
            sis_section_number=102,
            section_type="LAB",
        )
        existing_section.instructors.set([self.instructor])
        lecture_section.instructors.set([self.instructor])
        discussion_section.instructors.set([self.instructor])
        ScheduledCourse.objects.create(
            schedule=schedule,
            section=existing_section,
            instructor=self.instructor,
            enrolled_units=3,
        )

        post_url = reverse("schedule_add_course", args=[self.course.pk])
        response = self.client.post(
            post_url,
            {
                "schedule_id": str(schedule.pk),
                "selection": [
                    f"{lecture_section.pk}:{self.instructor.pk}",
                    f"{existing_section.pk}:{self.instructor.pk}",
                ],
                "semester": str(self.semester.pk),
                "next": reverse("schedule"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            ScheduledCourse.objects.filter(schedule=schedule).count(),
            1,
        )
        self.assertFalse(
            ScheduledCourse.objects.filter(
                schedule=schedule, section=lecture_section
            ).exists()
        )
