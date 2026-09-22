"""Quick-rate candidates: which courses to ask a user to rate, in what order."""

from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db.models import Count
from django.utils import timezone

from ..models import (
    Course,
    Instructor,
    QuickRateDismissal,
    Review,
    ScheduledCourse,
    Semester,
)
from ..utils import reviewable_semesters

# Below this many reviews, the row tells the user their rating matters most.
_SCARCE_REVIEW_COUNT = 5

# Session key under which the post-finals banner caches its candidate count
# for the day. Shared with tcf_core.context_processors and
# tcf_website.views.review.quick_rate (tcf_website must not import tcf_core).
QUICK_RATE_BANNER_SESSION_KEY = "quick_rate_banner"


@dataclass(frozen=True)
class Candidate:
    """One course–instructor pair the user probably took and has not rated."""

    course: Course
    instructor: Instructor
    semester: Semester
    review_count: int

    @property
    def reason(self) -> str:
        """Why this row is near the top, in the user's terms."""
        if self.review_count == 0:
            return "No reviews yet — be the first"
        if self.review_count < _SCARCE_REVIEW_COUNT:
            noun = "review" if self.review_count == 1 else "reviews"
            return f"Only {self.review_count} {noun} — yours counts most here"
        return f"{self.review_count} reviews"


def _review_counts(pairs) -> dict[tuple[int, int], int]:
    """Visible review count per (course_id, instructor_id)."""
    if not pairs:
        return {}
    rows = (
        Review.objects.filter(
            hidden=False,
            toxicity_rating__lt=settings.TOXICITY_THRESHOLD,
            course_id__in={course_id for course_id, _ in pairs},
            instructor_id__in={instructor_id for _, instructor_id in pairs},
        )
        .values("course_id", "instructor_id")
        .annotate(n=Count("id"))
    )
    return {(row["course_id"], row["instructor_id"]): row["n"] for row in rows}


def candidates_for(user, now=None) -> list[Candidate]:
    """Pairs from the user's past schedules they have not reviewed or dismissed.

    Ordered by fewest existing reviews, then most recent term. A term counts as
    past once it started ``QUICK_RATE_MIN_DAYS_INTO_TERM`` days ago. The
    threshold is measured from the first day of the term's start month, so it
    can fire a few weeks earlier than the literal day count.
    """
    now = now or timezone.now()
    cutoff = now - timedelta(days=settings.QUICK_RATE_MIN_DAYS_INTO_TERM)
    ratable_ids = set(reviewable_semesters(as_of=cutoff).values_list("pk", flat=True))

    scheduled = (
        ScheduledCourse.objects.filter(
            schedule__user=user,
            section__semester_id__in=ratable_ids,
            instructor__hidden=False,
        )
        .select_related(
            "section__course__subdepartment", "section__semester", "instructor"
        )
        .order_by("-section__semester__number")
    )

    # Same rule as is_duplicate_review_for_user: a review blocks its
    # (course, instructor) pair and its (course, semester) term.
    reviewed = list(
        user.review_set.filter(course__isnull=False).values_list(
            "course_id", "instructor_id", "semester_id"
        )
    )
    reviewed_pairs = {
        (course_id, instructor_id) for course_id, instructor_id, _ in reviewed
    }
    reviewed_terms = {
        (course_id, semester_id) for course_id, _, semester_id in reviewed
    }
    dismissed = set(
        QuickRateDismissal.objects.filter(user=user).values_list(
            "course_id", "instructor_id"
        )
    )

    picked: dict[tuple[int, int], tuple] = {}
    for item in scheduled:
        course = item.section.course
        semester = item.section.semester
        key = (course.id, item.instructor_id)
        if key in picked or key in reviewed_pairs or key in dismissed:
            continue
        if (course.id, semester.id) in reviewed_terms:
            continue
        picked[key] = (course, item.instructor, semester)

    counts = _review_counts(picked.keys())
    candidates = [
        Candidate(course, instructor, semester, counts.get(key, 0))
        for key, (course, instructor, semester) in picked.items()
    ]
    candidates.sort(key=lambda c: (c.review_count, -c.semester.number, c.course.id))
    return candidates
