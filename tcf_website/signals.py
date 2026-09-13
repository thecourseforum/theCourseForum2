"""Signal handlers that keep denormalized review stats in sync (issue #982).

A ``Review`` change (create / edit / delete) triggers a recompute-from-scratch of
the affected ``(course, instructor)`` pair stats and the course rollup. Registered
from ``TcfWebsiteConfig.ready``.

Editing a review can move it to a different course/instructor or flip ``hidden``;
to keep every affected aggregate correct we recompute the target recorded on the
instance *before* the save as well as the one after it.
"""

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import Review
from .models.stats import recompute_stats_for_review_target


def _remember_previous_target(instance: Review) -> None:
    """Stash the pre-save (course_id, instructor_id) on the instance, if it moved."""
    if not instance.pk:
        instance._tcf_previous_stats_target = None
        return
    previous = (
        Review.objects.filter(pk=instance.pk)
        .values("course_id", "instructor_id")
        .first()
    )
    if previous is None:
        instance._tcf_previous_stats_target = None
    else:
        instance._tcf_previous_stats_target = (
            previous["course_id"],
            previous["instructor_id"],
        )


@receiver(pre_save, sender=Review)
def _review_pre_save(sender, instance, **kwargs):
    """Capture the review's previous course/instructor before the row changes."""
    _remember_previous_target(instance)


@receiver(post_save, sender=Review)
def _review_post_save(sender, instance, **kwargs):
    """Recompute stats for the review's (new and, if moved, old) target."""
    recompute_stats_for_review_target(instance.course_id, instance.instructor_id)

    previous = getattr(instance, "_tcf_previous_stats_target", None)
    if previous and previous != (instance.course_id, instance.instructor_id):
        old_course_id, old_instructor_id = previous
        recompute_stats_for_review_target(old_course_id, old_instructor_id)


@receiver(post_delete, sender=Review)
def _review_post_delete(sender, instance, **kwargs):
    """Recompute stats for the deleted review's target."""
    recompute_stats_for_review_target(instance.course_id, instance.instructor_id)
