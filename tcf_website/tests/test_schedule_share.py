# pylint: disable=no-member
"""Tests for schedule sharing (bookmarks on /schedule) and comparison."""

import uuid

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Schedule, ScheduleBookmark
from .test_utils import setup


class ScheduleShareTestCase(TestCase):
    """Share links add bookmarks; comparison uses any visible schedule id."""

    def setUp(self):
        setup(self)
        self.client = Client()

    def test_add_shared_creates_bookmark_and_redirects(self):
        token = uuid.uuid4()
        sched = Schedule.objects.create(
            name="Friend",
            user=self.user1,
            semester=self.semester,
            share_token=token,
        )
        self.client.force_login(self.user2)
        url = f"{reverse('schedule')}?add_shared={token}"
        response = self.client.get(url, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ScheduleBookmark.objects.filter(viewer=self.user2, schedule=sched).exists()
        )

    def test_schedule_share_enable_sets_token(self):
        sched = Schedule.objects.create(
            name="A", user=self.user1, semester=self.semester, share_token=None
        )
        self.client.force_login(self.user1)
        self.client.post(
            reverse("schedule_share"),
            {
                "schedule_id": str(sched.pk),
                "action": "enable",
                "next": reverse("schedule"),
            },
        )
        sched.refresh_from_db()
        self.assertIsNotNone(sched.share_token)

    def test_schedule_share_wrong_user_redirects(self):
        sched = Schedule.objects.create(
            name="A", user=self.user1, semester=self.semester, share_token=None
        )
        self.client.force_login(self.user2)
        response = self.client.post(
            reverse("schedule_share"),
            {
                "schedule_id": str(sched.pk),
                "action": "enable",
                "next": reverse("schedule"),
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_compare_own_schedule_same_semester(self):
        s1 = Schedule.objects.create(
            name="One", user=self.user1, semester=self.semester
        )
        s2 = Schedule.objects.create(
            name="Two", user=self.user1, semester=self.semester
        )
        self.client.force_login(self.user1)
        url = (
            f"{reverse('schedule')}?semester={self.semester.pk}"
            f"&schedule={s1.pk}&compare={s2.pk}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["compare_schedule"].pk, s2.pk)

    def test_compare_bookmarked_schedule(self):
        token = uuid.uuid4()
        friend = Schedule.objects.create(
            name="Friend",
            user=self.user2,
            semester=self.semester,
            share_token=token,
        )
        mine = Schedule.objects.create(
            name="Mine", user=self.user1, semester=self.semester
        )
        ScheduleBookmark.objects.create(viewer=self.user1, schedule=friend)
        self.client.force_login(self.user1)
        url = (
            f"{reverse('schedule')}?semester={self.semester.pk}"
            f"&schedule={mine.pk}&compare={friend.pk}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["compare_schedule"].pk, friend.pk)

    def test_compare_invalid_id_shows_message(self):
        s1 = Schedule.objects.create(
            name="One", user=self.user1, semester=self.semester
        )
        self.client.force_login(self.user1)
        url = (
            f"{reverse('schedule')}?semester={self.semester.pk}"
            f"&schedule={s1.pk}&compare=999999"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "could not be loaded", status_code=200)

    def test_compare_overlap_sets_merged_calendar(self):
        s1 = Schedule.objects.create(
            name="One", user=self.user1, semester=self.semester
        )
        s2 = Schedule.objects.create(
            name="Two", user=self.user1, semester=self.semester
        )
        self.client.force_login(self.user1)
        url = (
            f"{reverse('schedule')}?semester={self.semester.pk}"
            f"&schedule={s1.pk}&compare={s2.pk}&overlap=1"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["merged_calendar"])

    def test_grid_partial_returns_only_grid_markup(self):
        s1 = Schedule.objects.create(
            name="One", user=self.user1, semester=self.semester
        )
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse("schedule"),
            {
                "semester": str(self.semester.pk),
                "schedule": str(s1.pk),
                "partial": "grid",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "schedule-builder__grid")
        self.assertContains(
            response,
            f'data-builder-active-semester="{self.semester.pk}"',
        )
        self.assertNotContains(response, "schedule-builder__title")

    def test_grid_partial_includes_compare_ui_when_compare_param(self):
        s1 = Schedule.objects.create(
            name="One", user=self.user1, semester=self.semester
        )
        s2 = Schedule.objects.create(
            name="Two", user=self.user1, semester=self.semester
        )
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse("schedule"),
            {
                "semester": str(self.semester.pk),
                "schedule": str(s1.pk),
                "compare": str(s2.pk),
                "partial": "grid",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "schedule-builder__grid")
        self.assertContains(response, "Exit compare")
        self.assertNotContains(response, "schedule-builder__title")

    def test_grid_partial_past_semester_preserves_compare(self):
        """Builder query with another term still renders compare when schedules match that term."""
        s1 = Schedule.objects.create(
            name="PastA", user=self.user1, semester=self.past_semester
        )
        s2 = Schedule.objects.create(
            name="PastB", user=self.user1, semester=self.past_semester
        )
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse("schedule"),
            {
                "semester": str(self.past_semester.pk),
                "schedule": str(s1.pk),
                "compare": str(s2.pk),
                "partial": "grid",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Exit compare")

    def test_compare_pick_partial_returns_apply_buttons(self):
        s1 = Schedule.objects.create(
            name="One", user=self.user1, semester=self.semester
        )
        s2 = Schedule.objects.create(
            name="Two", user=self.user1, semester=self.semester
        )
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse("schedule"),
            {
                "semester": str(self.semester.pk),
                "schedule": str(s1.pk),
                "partial": "compare_pick",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-schedule-apply-compare")
        self.assertContains(response, "Two")

    def test_duplicate_schedule_clears_share_token(self):
        token = uuid.uuid4()
        sched = Schedule.objects.create(
            name="Orig",
            user=self.user1,
            semester=self.semester,
            share_token=token,
        )
        self.client.force_login(self.user1)
        self.client.post(
            reverse("duplicate_schedule", args=[sched.pk]),
            {"next": reverse("schedule")},
        )
        dup = Schedule.objects.exclude(pk=sched.pk).get(
            user=self.user1, semester=self.semester, name__startswith="Copy of"
        )
        self.assertIsNone(dup.share_token)
