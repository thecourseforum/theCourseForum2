"""Review-related queries and small pure helpers."""

from ..models import Instructor
from ..utils import recent_semesters


def recent_semester_id_set() -> set[int]:
    return set(recent_semesters().values_list("pk", flat=True))


def club_semester_choices_payload():
    """JSON-serializable term rows for club-mode review (inline club pick)."""
    return [{"id": s.id, "label": str(s)} for s in recent_semesters()]


def instructors_for_course_semester(course_id: int, semester_id: int):
    """Instructors with a section for this course in this semester."""
    return (
        Instructor.objects.filter(
            section__course_id=course_id,
            section__semester_id=semester_id,
            hidden=False,
        )
        .distinct()
        .order_by("last_name", "first_name")
    )


def is_duplicate_review_for_user(user, instance) -> bool:
    """True if this user already has a conflicting review for the same target."""
    if instance.club:
        return user.review_set.filter(club=instance.club).exists()

    if user.review_set.filter(
        course=instance.course, semester=instance.semester
    ).exists():
        return True

    if user.review_set.filter(
        course=instance.course, instructor=instance.instructor
    ).exists():
        return True

    return False
