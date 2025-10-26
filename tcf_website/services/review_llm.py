"""Utilities to keep LLM powered review summaries fresh"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Iterable, List, Optional

import boto3
import botocore.exceptions
from django.conf import settings
from django.db import close_old_connections, transaction
from django.db.models import Avg, Count, Q, QuerySet
from django.utils import timezone
from django.utils.text import Truncator

from ..models import Club, Course, Instructor, Review, ReviewLLMSummary

logger = logging.getLogger(__name__)

LLM_MODEL_ID = getattr(settings, "BEDROCK_MODEL_ID", "amazon.titan-text-lite-v1")
TRIGGER_DELTA = getattr(settings, "AI_SUMMARY_MIN_NEW_REVIEWS", 3)
MAX_REVIEWS_IN_PROMPT = getattr(settings, "AI_SUMMARY_MAX_REVIEWS", 12)
MAX_REVIEW_SNIPPET_CHARS = getattr(settings, "AI_SUMMARY_REVIEW_SNIPPET_CHARS", 350)


@dataclass(frozen=True)
class SummaryTarget:
    """Represents the entity we are summarising."""

    course_id: Optional[int] = None
    instructor_id: Optional[int] = None
    club_id: Optional[int] = None

    @property
    def is_club(self) -> bool:
        return self.club_id is not None

    def validate(self) -> None:
        if self.is_club:
            if self.course_id or self.instructor_id:
                raise ValueError("Club summaries cannot include course or instructor.")
        else:
            if not (self.course_id and self.instructor_id):
                raise ValueError("Course summaries require both course and instructor.")


def maybe_schedule_summary_generation(
    review: Review, llm_client: Optional[Callable[[List[dict]], str]] = None
) -> None:
    """Schedule a background refresh if the review unlocks a new summary."""

    if not review.text or review.hidden:
        return

    if review.club_id:
        target = SummaryTarget(club_id=review.club_id)
    elif review.course_id and review.instructor_id:
        target = SummaryTarget(
            course_id=review.course_id,
            instructor_id=review.instructor_id,
        )
    else:
        return

    if not getattr(settings, "BEDROCK_SUMMARY_ENABLED", False):
        logger.debug("Skipping LLM summary refresh: Bedrock summaries disabled.")
        return

    target.validate()

    def _task():
        close_old_connections()
        try:
            _refresh_summary(target, llm_client=llm_client)
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "Failed to refresh LLM summary for target %s", vars(target)
            )
        finally:
            close_old_connections()

    transaction.on_commit(
        lambda: threading.Thread(target=_task, daemon=True, name="llm-summary").start()
    )


def refresh_summary_now(
    target: SummaryTarget, llm_client: Optional[Callable[[List[dict]], str]] = None
) -> None:
    """Synchronously refresh the summary for the provided target.

    Useful for tests and management commands.
    """

    target.validate()
    _refresh_summary(target, llm_client=llm_client)


def _refresh_summary(
    target: SummaryTarget,
    llm_client: Optional[Callable[[List[dict]], str]] = None,
) -> None:
    """Refresh the summary if enough new reviews have arrived."""

    llm_client = llm_client or _call_bedrock

    queryset = _eligible_reviews(target)
    total_reviews = queryset.count()
    if total_reviews == 0:
        logger.debug("No eligible reviews for summary target %s", vars(target))
        return

    summary_record = _ensure_summary_record(target)

    if summary_record.summary_text:
        new_reviews_qs = queryset.filter(id__gt=summary_record.last_review_id)
        new_reviews_count = new_reviews_qs.count()
        if new_reviews_count < TRIGGER_DELTA:
            logger.debug(
                "Only %s new reviews for target %s (need %s); skipping refresh.",
                new_reviews_count,
                vars(target),
                TRIGGER_DELTA,
            )
            return
        reviews_for_prompt = list(
            new_reviews_qs.order_by("id")[:MAX_REVIEWS_IN_PROMPT]
        )
        prior_summary = summary_record.summary_text
    else:
        if total_reviews < TRIGGER_DELTA:
            logger.debug(
                "Only %s total reviews for target %s (need %s); skipping initial summary.",
                total_reviews,
                vars(target),
                TRIGGER_DELTA,
            )
            return
        reviews_for_prompt = list(
            queryset.order_by("-id")[:MAX_REVIEWS_IN_PROMPT][::-1]
        )
        prior_summary = ""

    prompt_payload = _build_prompt_payload(
        target=target,
        reviews=reviews_for_prompt,
        total_reviews=total_reviews,
        prior_summary=prior_summary,
    )

    generated_text = llm_client(prompt_payload.messages)
    if not generated_text:
        logger.warning("Received empty summary text for target %s", vars(target))
        return

    latest_processed_id = max(review.id for review in reviews_for_prompt)
    summary_record.summary_text = generated_text.strip()
    summary_record.model_id = LLM_MODEL_ID
    summary_record.source_review_count = total_reviews
    summary_record.last_review_id = latest_processed_id
    summary_record.source_metadata = prompt_payload.metadata
    summary_record.save(
        update_fields=[
            "summary_text",
            "model_id",
            "source_review_count",
            "last_review_id",
            "source_metadata",
            "updated_at",
        ]
    )

    logger.info(
        "Updated LLM summary for target %s using %s new reviews.",
        vars(target),
        len(reviews_for_prompt),
    )


@dataclass
class PromptPayload:
    messages: List[dict]
    metadata: dict


def _build_prompt_payload(
    target: SummaryTarget,
    reviews: Iterable[Review],
    total_reviews: int,
    prior_summary: str,
) -> PromptPayload:
    entity_info = _target_info(target)

    stats = _compute_stats(target)

    review_entries = [
        {
            "id": review.id,
            "created": timezone.localtime(review.created).isoformat(),
            "ratings": {
                "instructor": review.instructor_rating,
                "recommendability": review.recommendability,
                "enjoyability": review.enjoyability,
                "difficulty": review.difficulty,
                "hours_per_week": review.hours_per_week,
            },
            "snippet": Truncator(review.text).chars(
                MAX_REVIEW_SNIPPET_CHARS, truncate="…"
            ),
        }
        for review in reviews
    ]

    user_payload = {
        "entity": entity_info,
        "total_review_count": total_reviews,
        "stats": stats,
        "previous_summary": prior_summary or None,
        "new_reviews": review_entries,
        "instructions": {
            "style": "Neutral, concise, factual.",
            "sections": [
                "Overall sentiment",
                "Highlights",
                "Common pain points",
                "Workload expectations",
            ],
            "length_target_words": 140,
        },
    }

    messages = [
        {
            "role": "system",
            "content": (
                "You summarize university course reviews for students. "
                "Stay brief, neutral, concise, and avoid exaggeration. "
                "You output summarizes in a single paragraph form. "
                "Base every claim on the provided reviews or stats."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(user_payload, indent=2),
        },
    ]

    metadata = {
        "review_ids": [entry["id"] for entry in review_entries],
        "stats": stats,
        "generated_at": timezone.now().isoformat(),
    }

    return PromptPayload(messages=messages, metadata=metadata)


def _target_info(target: SummaryTarget) -> dict:
    if target.is_club:
        club = Club.objects.get(id=target.club_id)
        return {
            "type": "club",
            "name": club.name,
            "category": club.category.name if club.category else None,
        }
    course = Course.objects.get(id=target.course_id)
    instructor = Instructor.objects.get(id=target.instructor_id)
    return {
        "type": "course_instructor",
        "course": {
            "code": course.code(),
            "title": course.title,
        },
        "instructor": {
            "full_name": instructor.full_name,
        },
    }


def _eligible_reviews(target: SummaryTarget) -> QuerySet[Review]:
    filters = {"text__isnull": False}
    if target.is_club:
        filters["club_id"] = target.club_id
    else:
        filters["course_id"] = target.course_id
        filters["instructor_id"] = target.instructor_id

    queryset = (
        Review.objects.filter(
            hidden=False,
            toxicity_rating__lt=settings.TOXICITY_THRESHOLD,
            **filters,
        )
        .exclude(text="")
        .order_by("id")
    )
    return queryset


def _ensure_summary_record(target: SummaryTarget) -> ReviewLLMSummary:
    with transaction.atomic():
        if target.is_club:
            summary = (
                ReviewLLMSummary.objects.select_for_update()
                .filter(club_id=target.club_id)
                .first()
            )
            if summary:
                return summary
            return ReviewLLMSummary.objects.create(club_id=target.club_id)
        summary = (
            ReviewLLMSummary.objects.select_for_update()
            .filter(
                course_id=target.course_id,
                instructor_id=target.instructor_id,
                club__isnull=True,
            )
            .first()
        )
        if summary:
            return summary
        return ReviewLLMSummary.objects.create(
            course_id=target.course_id,
            instructor_id=target.instructor_id,
        )


def _compute_stats(target: SummaryTarget) -> dict:
    queryset = _eligible_reviews(target)
    aggregates = queryset.aggregate(
        average_instructor=Avg("instructor_rating"),
        average_enjoyability=Avg("enjoyability"),
        average_recommendability=Avg("recommendability"),
        average_difficulty=Avg("difficulty"),
        average_hours=Avg("hours_per_week"),
        review_count=Count("id"),
        text_review_count=Count("id", filter=~Q(text="")),
    )
    for key, value in aggregates.items():
        if isinstance(value, float):
            aggregates[key] = round(value, 2)
    return aggregates


def _call_bedrock(messages: List[dict]) -> str:
    """Invoke AWS Bedrock to generate a summary."""

    prompt_parts = []
    for message in messages:
        role = message.get("role", "").upper()
        content = message.get("content", "")
        prompt_parts.append(f"{role}:\n{content}")
    prompt = "\n\n".join(prompt_parts) + "\n\nASSISTANT:\n"

    body = json.dumps(
        {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 400,
                "temperature": 0.4,
                "topP": 0.9,
                "stopSequences": ["</END>"],
            },
        }
    )

    try:
        client = _bedrock_client()
        response = client.invoke_model(
            modelId=LLM_MODEL_ID,
            body=body,
            accept="application/json",
            contentType="application/json",
        )
        payload = json.loads(response["body"].read())
        results = payload.get("results") or []
        if not results:
            return ""
        return results[0].get("outputText", "").strip()
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as exc:
        logger.exception("Bedrock invocation failed: %s", exc)
        return ""


@lru_cache(maxsize=1)
def _bedrock_client():
    """Create (and cache) a Bedrock runtime client."""
    region = getattr(settings, "BEDROCK_REGION", "us-east-1")
    return boto3.client("bedrock-runtime", region_name=region)
