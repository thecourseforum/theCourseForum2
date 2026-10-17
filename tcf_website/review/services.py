"""Review-related queries and small pure helpers."""

import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings

from ..models import Instructor
from ..utils import recent_semesters


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


def get_review_text(review):
    """Return the text of a review, or None if it has no text."""
    if review.text:
        return review.text
    return None


logger = logging.getLogger(__name__)


def moderate_review(text: str) -> str | None:
    """Send review text to Nova Micro and return its response."""
    if not text or not getattr(settings, "ENABLE_REVIEW_MODERATION", False):
        return None

    try:
        client = boto3.client("bedrock-runtime", region_name="us-east-1")

        response = client.converse(
            modelId="amazon.nova-micro-v1:0",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": (
                                "Classify this course review as Appropriate or "
                                "Inappropriate based on whether it contains "
                                "toxic, abusive, or derogatory language. "
                                "Respond with only the classification.\n\n"
                                f"Review: {text}"
                            )
                        }
                    ],
                }
            ],
            inferenceConfig={"maxTokens": 20, "temperature": 0},
        )

        return response["output"]["message"]["content"][0]["text"]

    except (BotoCoreError, ClientError, OSError):
        logger.exception("Bedrock review moderation request failed")
        return None
