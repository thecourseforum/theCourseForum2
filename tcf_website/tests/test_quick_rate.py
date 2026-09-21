"""Tests for the quick-rate candidate service and views."""

from datetime import UTC, datetime

from django.test import TestCase
from django.urls import reverse

from ..models import (
    QuickRateDismissal,
    Review,
    Schedule,
    ScheduledCourse,
    Section,
    Semester,
)
from ..review.quick_rate import Candidate, candidates_for
from .test_utils import setup

# Well after Fall 2025 (the fixture semester) is 70 days old.
NOW = datetime(2026, 3, 1, tzinfo=UTC)


def schedule_course(user, section, instructor, name="Plan A"):
    """Put `section` on a schedule for `user`."""
    schedule = Schedule.objects.create(name=name, user=user, semester=section.semester)
    return ScheduledCourse.objects.create(
        schedule=schedule, section=section, instructor=instructor, time=""
    )


class CandidatesForTests(TestCase):
    """candidates_for turns schedule history into an ordered list."""

    def setUp(self):
        setup(self)
        # user4 has no reviews. Fixture: `course` has reviews, `course2` has
        # reviews, both taught by `instructor` in Fall 2025.
        schedule_course(self.user4, self.section_course, self.instructor)
        schedule_course(self.user4, self.section_course2, self.instructor)

    def test_lists_scheduled_courses_fewest_reviews_first(self):
        # Fixture gives `course` and `course2` 2 visible reviews each
        # (test_utils.setup: review1/review2 on `course`, review3/review4 on
        # `course2`). Add one more visible review on `course` so the counts
        # differ and the order is determined.
        Review.objects.create(
            user=self.user3,
            course=self.course,
            instructor=self.instructor,
            semester=self.semester,
            text="",
            instructor_rating=4,
            difficulty=3,
            recommendability=4,
            enjoyability=4,
            hours_per_week=5,
        )
        result = candidates_for(self.user4, now=NOW)
        self.assertEqual(
            [c.course.id for c in result], [self.course2.id, self.course.id]
        )
        self.assertEqual([c.review_count for c in result], [2, 3])

    def test_excludes_pairs_the_user_already_reviewed(self):
        # user1 reviewed `course` and `course2` in the fixture.
        schedule_course(self.user1, self.section_course, self.instructor)
        schedule_course(self.user1, self.section_course2, self.instructor)
        self.assertEqual(candidates_for(self.user1, now=NOW), [])

    def test_excludes_dismissed_pairs(self):
        QuickRateDismissal.objects.create(
            user=self.user4, course=self.course, instructor=self.instructor
        )
        result = candidates_for(self.user4, now=NOW)
        self.assertEqual([c.course.id for c in result], [self.course2.id])

    def test_dedupes_across_draft_schedules(self):
        schedule_course(self.user4, self.section_course, self.instructor, name="Plan B")
        result = candidates_for(self.user4, now=NOW)
        self.assertEqual(len(result), 2)

    def test_excludes_terms_less_than_70_days_old(self):
        fall_2026 = Semester.objects.create(year=2026, season="FALL", number=1268)
        section = Section.objects.create(
            course=self.course3, semester=fall_2026, sis_section_number=99001
        )
        section.instructors.add(self.instructor)
        schedule_course(self.user4, section, self.instructor)

        early = datetime(2026, 9, 21, tzinfo=UTC)
        self.assertNotIn(
            self.course3.id,
            [c.course.id for c in candidates_for(self.user4, now=early)],
        )
        late = datetime(2026, 11, 1, tzinfo=UTC)
        self.assertIn(
            self.course3.id, [c.course.id for c in candidates_for(self.user4, now=late)]
        )

    def test_reason_text(self):
        self.assertEqual(
            Candidate(self.course, self.instructor, self.semester, 0).reason,
            "No reviews yet — be the first",
        )
        self.assertEqual(
            Candidate(self.course, self.instructor, self.semester, 1).reason,
            "Only 1 review — yours counts most here",
        )
        self.assertEqual(
            Candidate(self.course, self.instructor, self.semester, 4).reason,
            "Only 4 reviews — yours counts most here",
        )
        self.assertEqual(
            Candidate(self.course, self.instructor, self.semester, 5).reason,
            "5 reviews",
        )


class QuickRateViewTests(TestCase):
    """The quick-rate page and its two POST endpoints."""

    def setUp(self):
        setup(self)
        schedule_course(self.user4, self.section_course2, self.instructor)

    def _payload(self, **overrides):
        data = {
            "course": self.course2.id,
            "instructor": self.instructor.id,
            "semester": self.semester.id,
            "instructor_rating": 4,
            "difficulty": 3,
            "recommendability": 5,
            "enjoyability": 4,
            "hours_per_week": 6,
        }
        data.update(overrides)
        return data

    def test_page_requires_login(self):
        response = self.client.get(reverse("quick_rate"))
        self.assertEqual(response.status_code, 302)

    def test_page_lists_candidates(self):
        self.client.force_login(self.user4)
        response = self.client.get(reverse("quick_rate"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [c.course.id for c in response.context["candidates"]], [self.course2.id]
        )
        self.assertEqual(response.context["rated_count"], 0)

    def test_adhoc_course_gets_semester_choices(self):
        self.client.force_login(self.user4)
        response = self.client.get(reverse("quick_rate"), {"course": self.course.id})
        self.assertEqual(response.context["adhoc_course"], self.course)
        self.assertIn(self.semester, list(response.context["adhoc_semesters"]))

    def test_non_numeric_course_is_ignored(self):
        self.client.force_login(self.user4)
        response = self.client.get(reverse("quick_rate"), {"course": "abc"})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["adhoc_course"])

    def test_submit_creates_ratings_only_review(self):
        self.client.force_login(self.user4)
        response = self.client.post(reverse("quick_rate_submit"), self._payload())
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertFalse(body["has_text"])
        review = Review.objects.get(pk=body["review_id"])
        self.assertEqual(review.user, self.user4)
        self.assertEqual(review.text, "")
        self.assertEqual(review.hours_per_week, 6)

    def test_submit_rejects_duplicate(self):
        self.client.force_login(self.user4)
        self.client.post(reverse("quick_rate_submit"), self._payload())
        response = self.client.post(reverse("quick_rate_submit"), self._payload())
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            Review.objects.filter(user=self.user4, course=self.course2).count(), 1
        )

    def test_submit_rejects_invalid(self):
        self.client.force_login(self.user4)
        payload = self._payload()
        del payload["difficulty"]
        response = self.client.post(reverse("quick_rate_submit"), payload)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])

    def test_submit_requires_post(self):
        self.client.force_login(self.user4)
        response = self.client.get(reverse("quick_rate_submit"))
        self.assertEqual(response.status_code, 405)

    def test_dismiss_is_idempotent_and_hides_candidate(self):
        self.client.force_login(self.user4)
        data = {"course": self.course2.id, "instructor": self.instructor.id}
        self.assertEqual(
            self.client.post(reverse("quick_rate_dismiss"), data).status_code, 200
        )
        self.assertEqual(
            self.client.post(reverse("quick_rate_dismiss"), data).status_code, 200
        )
        self.assertEqual(QuickRateDismissal.objects.filter(user=self.user4).count(), 1)
        response = self.client.get(reverse("quick_rate"))
        self.assertEqual(response.context["candidates"], [])

    def test_dismiss_rejects_bad_input(self):
        self.client.force_login(self.user4)
        response = self.client.post(reverse("quick_rate_dismiss"), {"course": "x"})
        self.assertEqual(response.status_code, 400)

    def test_dismiss_rejects_nonexistent_ids(self):
        self.client.force_login(self.user4)
        response = self.client.post(
            reverse("quick_rate_dismiss"),
            {"course": 999999, "instructor": self.instructor.id},
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])

        response = self.client.post(
            reverse("quick_rate_dismiss"),
            {"course": self.course2.id, "instructor": 999999},
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])

        self.assertEqual(QuickRateDismissal.objects.filter(user=self.user4).count(), 0)
