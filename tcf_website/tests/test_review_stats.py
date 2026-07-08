"""Tests for denormalized review statistics (issue #982).

Covers signal-driven maintenance of CourseStats / CourseInstructorStats on review
create / edit / delete, hidden-review exclusion, stored-vs-live equivalence, and the
``recompute_review_stats`` backfill command.
"""

from django.core.management import call_command
from django.test import TestCase

from ..models import (
    CourseInstructorStats,
    CourseStats,
    Review,
)
from .test_utils import setup


class ReviewStatsSignalTests(TestCase):
    """Signals keep stored stats in sync with reviews."""

    def setUp(self):
        setup(self)

    def test_course_stats_created_on_review_create(self):
        """Creating reviews (in setup) populates a CourseStats row."""
        stats = CourseStats.objects.get(course=self.course)
        # course has review1 + review2 (both non-hidden).
        self.assertEqual(stats.review_count, 2)
        expected_difficulty = (self.review1.difficulty + self.review2.difficulty) / 2
        self.assertAlmostEqual(stats.average_difficulty, expected_difficulty, places=4)

    def test_course_instructor_stats_created(self):
        """A (course, instructor) stats row is populated for the pair."""
        stats = CourseInstructorStats.objects.get(
            course=self.course, instructor=self.instructor
        )
        self.assertEqual(stats.review_count, 2)

    def test_stored_matches_live_rating(self):
        """Course.average_rating() (stored) equals the historic live formula."""
        expected = (self.review1.average() + self.review2.average()) / 2
        self.assertAlmostEqual(self.course.average_rating(), expected, places=4)

    def test_instructor_stored_matches_live(self):
        """Instructor per-course averages read from stored stats correctly."""
        expected_difficulty = (self.review1.difficulty + self.review2.difficulty) / 2
        self.assertAlmostEqual(
            self.instructor.average_difficulty_for_course(self.course),
            expected_difficulty,
            places=4,
        )
        expected_reading = (
            self.review1.amount_reading + self.review2.amount_reading
        ) / 2
        self.assertAlmostEqual(
            self.instructor.average_reading_hours_for_course(self.course),
            expected_reading,
            places=4,
        )

    def test_stats_update_on_review_edit(self):
        """Editing a review recomputes the stored averages."""
        self.review1.difficulty = 3
        self.review1.save()
        stats = CourseStats.objects.get(course=self.course)
        expected = (3 + self.review2.difficulty) / 2
        self.assertAlmostEqual(stats.average_difficulty, expected, places=4)

    def test_stats_removed_when_last_review_deleted(self):
        """Deleting all reviews removes the stats rows (no stale data)."""
        self.review1.delete()
        self.review2.delete()
        self.assertFalse(CourseStats.objects.filter(course=self.course).exists())
        self.assertFalse(
            CourseInstructorStats.objects.filter(
                course=self.course, instructor=self.instructor
            ).exists()
        )
        # Read path falls back to live computation → None with no reviews.
        self.assertIsNone(self.course.average_rating())
        self.assertIsNone(self.course.average_difficulty())

    def test_hidden_review_excluded(self):
        """Hidden reviews do not contribute to the stored averages."""
        self.review1.hidden = True
        self.review1.save()
        stats = CourseStats.objects.get(course=self.course)
        self.assertEqual(stats.review_count, 1)
        self.assertAlmostEqual(
            stats.average_difficulty, self.review2.difficulty, places=4
        )

    def test_review_move_updates_both_targets(self):
        """Re-pointing a review to another course fixes both old and new stats."""
        # review1/review2 are on self.course; move review1 to self.course2.
        self.review1.course = self.course2
        self.review1.save()

        old_stats = CourseStats.objects.get(course=self.course)
        self.assertEqual(old_stats.review_count, 1)  # only review2 remains

        new_stats = CourseStats.objects.get(course=self.course2)
        # course2 originally had review3 + review4; now also review1.
        self.assertEqual(new_stats.review_count, 3)


class RecomputeReviewStatsCommandTests(TestCase):
    """The backfill command rebuilds all stats from existing reviews."""

    def setUp(self):
        setup(self)

    def test_backfill_matches_signal_maintained_state(self):
        """After wiping and re-running the command, stats match live aggregates."""
        # Wipe stored rows to simulate a pre-backfill DB.
        CourseStats.objects.all().delete()
        CourseInstructorStats.objects.all().delete()

        call_command("recompute_review_stats")

        # Every course with non-hidden reviews should now have a stats row whose
        # difficulty matches a direct live aggregate.
        for review in Review.objects.filter(hidden=False):
            stats = CourseStats.objects.get(course=review.course)
            live = Review.objects.filter(
                course=review.course, hidden=False
            ).values_list("difficulty", flat=True)
            self.assertAlmostEqual(
                stats.average_difficulty, sum(live) / len(live), places=4
            )

    def test_backfill_creates_expected_pair_rows(self):
        """Backfill creates one CourseInstructorStats per (course, instructor) pair."""
        CourseInstructorStats.objects.all().delete()
        call_command("recompute_review_stats")
        # instructor teaches course, course2, course3, course4 (reviews 1-6).
        pairs = set(
            Review.objects.filter(hidden=False)
            .exclude(course__isnull=True)
            .exclude(instructor__isnull=True)
            .values_list("course_id", "instructor_id")
        )
        self.assertEqual(CourseInstructorStats.objects.count(), len(pairs))
