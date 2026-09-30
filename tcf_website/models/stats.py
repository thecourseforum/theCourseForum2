"""Denormalized review-statistics maintenance (issue #982).

Historically a course's average review data (rating components, difficulty, hours
breakdowns, etc.) was aggregated from every ``Review`` on every request. These
helpers instead maintain those aggregates on the ``CourseStats`` and
``CourseInstructorStats`` models, recomputing from scratch for the affected
``(course, instructor)`` pair and the course rollup whenever a review changes.

Recompute-from-scratch (rather than incremental add/subtract) is deliberate: it is
simple, always correct, and cheap because each recompute aggregates only the
reviews for a single course (or course+instructor), not the whole table.

GPA/grade averages are handled separately by ``load_grades`` and are out of scope.
"""

from django.db.models import Aggregate, Avg, Count

# Maps stats-model column -> the Review field it averages.
_STAT_COLUMN_TO_REVIEW_FIELD = {
    "average_instructor_rating": "instructor_rating",
    "average_difficulty": "difficulty",
    "average_recommendability": "recommendability",
    "average_enjoyability": "enjoyability",
    "average_hours_per_week": "hours_per_week",
    "average_amount_reading": "amount_reading",
    "average_amount_writing": "amount_writing",
    "average_amount_group": "amount_group",
    "average_amount_homework": "amount_homework",
}


def _aggregate_review_stats(review_qs) -> dict:
    """Return a dict of ``{stats_column: value}`` for the given review queryset.

    ``review_count`` is the number of (non-hidden) rows; each average column is the
    ``Avg`` of the corresponding Review field, or ``None`` when there are no rows.
    """
    aggregates: dict[str, Aggregate] = {"review_count": Count("id")}
    for column, review_field in _STAT_COLUMN_TO_REVIEW_FIELD.items():
        aggregates[column] = Avg(review_field)
    result = review_qs.aggregate(**aggregates)
    # ``Count`` yields 0 (not None) for an empty queryset.
    result["review_count"] = result.get("review_count") or 0
    return result


def recompute_course_instructor_stats(course_id: int, instructor_id: int) -> None:
    """Recompute stored stats for a single ``(course, instructor)`` pair.

    When no non-hidden reviews remain for the pair, the stats row is deleted so
    stale rows do not linger.
    """
    # Imported lazily to avoid a circular import (models.py imports this module's
    # sibling only at call time via signals/commands).
    from .models import CourseInstructorStats, Review

    if course_id is None or instructor_id is None:
        return

    review_qs = Review.objects.filter(
        course_id=course_id, instructor_id=instructor_id, hidden=False
    )
    values = _aggregate_review_stats(review_qs)

    if values["review_count"] == 0:
        CourseInstructorStats.objects.filter(
            course_id=course_id, instructor_id=instructor_id
        ).delete()
        return

    CourseInstructorStats.objects.update_or_create(
        course_id=course_id, instructor_id=instructor_id, defaults=values
    )


def recompute_course_stats(course_id: int) -> None:
    """Recompute the course-level rollup across all instructors.

    When no non-hidden reviews remain for the course, the stats row is deleted.
    """
    from .models import CourseStats, Review

    if course_id is None:
        return

    review_qs = Review.objects.filter(course_id=course_id, hidden=False)
    values = _aggregate_review_stats(review_qs)

    if values["review_count"] == 0:
        CourseStats.objects.filter(course_id=course_id).delete()
        return

    CourseStats.objects.update_or_create(course_id=course_id, defaults=values)


def recompute_stats_for_review_target(course_id, instructor_id) -> None:
    """Refresh both the pair stats and the course rollup for a changed review.

    Safe to call with ``None`` ids (club reviews, or reviews missing a course /
    instructor): the individual recompute helpers no-op on ``None``.
    """
    recompute_course_instructor_stats(course_id, instructor_id)
    recompute_course_stats(course_id)


def recompute_all_stats(*, verbose_writer=None) -> dict:
    """Backfill every stats row from existing reviews (used by the command).

    Rebuilds all ``CourseInstructorStats`` and ``CourseStats`` rows from scratch:
    deletes existing rows, then repopulates from non-hidden reviews grouped by
    course/instructor. Returns a summary dict of counts written.

    ``verbose_writer`` is an optional callable (e.g. the command's ``stdout.write``)
    used for progress output.
    """
    from .models import CourseInstructorStats, CourseStats, Review

    def _write(msg):
        if verbose_writer is not None:
            verbose_writer(msg)

    # Start clean so pairs/courses that lost all their reviews don't keep stale rows.
    _write("Clearing existing review-stat rows...")
    CourseInstructorStats.objects.all().delete()
    CourseStats.objects.all().delete()

    non_hidden = Review.objects.filter(hidden=False)

    # --- Per (course, instructor) pair ---------------------------------------
    pair_aggregates: dict[str, Aggregate] = {"review_count": Count("id")}
    for column, review_field in _STAT_COLUMN_TO_REVIEW_FIELD.items():
        pair_aggregates[column] = Avg(review_field)

    pair_rows = (
        non_hidden.exclude(course__isnull=True)
        .exclude(instructor__isnull=True)
        .values("course_id", "instructor_id")
        .annotate(**pair_aggregates)
    )
    pair_objs = [
        CourseInstructorStats(
            course_id=row["course_id"],
            instructor_id=row["instructor_id"],
            **{
                column: row[column]
                for column in ("review_count", *_STAT_COLUMN_TO_REVIEW_FIELD)
            },
        )
        for row in pair_rows
    ]
    CourseInstructorStats.objects.bulk_create(pair_objs, batch_size=2000)
    _write(f"Wrote {len(pair_objs)} CourseInstructorStats rows.")

    # --- Course-level rollup --------------------------------------------------
    course_rows = (
        non_hidden.exclude(course__isnull=True)
        .values("course_id")
        .annotate(**pair_aggregates)
    )
    course_objs = [
        CourseStats(
            course_id=row["course_id"],
            **{
                column: row[column]
                for column in ("review_count", *_STAT_COLUMN_TO_REVIEW_FIELD)
            },
        )
        for row in course_rows
    ]
    CourseStats.objects.bulk_create(course_objs, batch_size=2000)
    _write(f"Wrote {len(course_objs)} CourseStats rows.")

    return {
        "course_instructor_stats": len(pair_objs),
        "course_stats": len(course_objs),
    }
