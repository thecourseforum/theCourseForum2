"""Review-related queries and small pure helpers."""

from django.conf import settings

from ..models import Instructor
from ..utils import recent_semesters

# Toxicity categories mirror the (removed) evaluate_review_toxicity batch command
# and the display filters that hide reviews with toxicity_rating >= TOXICITY_THRESHOLD.
_TOXICITY_CATEGORIES = [
    "obscene",
    "threat",
    "insult",
    "identity_attack",
]

# Cache the Detoxify model so we only pay initialization cost once per process.
_detoxify_model = None
_detoxify_unavailable = False


def recent_semester_id_set() -> set[int]:
    """Primary keys of semesters in the recent-catalog window."""
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

    return (
        user.review_set.filter(
            course=instance.course, semester=instance.semester
        ).exists()
        or user.review_set.filter(
            course=instance.course, instructor=instance.instructor
        ).exists()
    )


def _get_detoxify_model():
    """Lazily load and cache the Detoxify model.

    Returns None when detoxify is not installed. Detoxify is an optional,
    heavyweight dependency (see requirements history); it is deliberately not a
    hard dependency of the web app. When absent we simply cannot score text
    synchronously, and callers must treat the review as not-flagged so
    submission is never blocked.
    """
    global _detoxify_model, _detoxify_unavailable
    if _detoxify_model is not None:
        return _detoxify_model
    if _detoxify_unavailable:
        return None
    try:
        import importlib  # pylint: disable=import-outside-toplevel

        # Dynamic import: detoxify is an optional dependency that is intentionally
        # not installed, so import it via importlib to avoid a hard static import.
        detoxify = importlib.import_module("detoxify")
        _detoxify_model = detoxify.Detoxify("original")
    except Exception:  # pylint: disable=broad-except
        # ImportError if not installed, or any model-init/runtime error.
        _detoxify_unavailable = True
        return None
    return _detoxify_model


def score_review_toxicity(text: str):
    """Score review text and return (rating, category).

    ``rating`` is on the same 0-100 scale used by ``toxicity_rating`` and the
    ``TOXICITY_THRESHOLD`` display filter (rating = round(100 * toxicity)).
    ``category`` is the most relevant toxicity label, or "" when there is no
    text or scoring is unavailable. Mirrors the removed evaluate_review_toxicity
    batch command so the pre-submission warning matches display filtering.

    Returns ``(0, "")`` when there is no text or Detoxify is unavailable, so the
    caller treats the review as not-flagged and never blocks submission.
    """
    if not text or not text.strip():
        return 0, ""

    model = _get_detoxify_model()
    if model is None:
        return 0, ""

    try:
        prediction = model.predict(text)
    except Exception:  # pylint: disable=broad-except
        return 0, ""

    rating = round(100 * prediction["toxicity"])
    category = max(
        _TOXICITY_CATEGORIES,
        key=lambda label: prediction.get(label, 0),
    )
    return rating, category


def review_will_be_hidden_for_toxicity(text: str) -> bool:
    """True if a review with this text would be hidden by the toxicity filter.

    Matches the display filter used everywhere reviews are shown:
    ``toxicity_rating >= settings.TOXICITY_THRESHOLD`` are hidden.
    """
    rating, _ = score_review_toxicity(text)
    return rating >= settings.TOXICITY_THRESHOLD
