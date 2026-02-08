"""Helpers for generating AI summaries of course/instructor reviews."""

from __future__ import annotations

from typing import Iterable, Tuple

import requests
from django.conf import settings

from ..models import Review

SUMMARY_THRESHOLD = 5
MAX_REVIEWS_FOR_PROMPT = 20
MAX_REVIEW_CHARS = 500


def _build_prompt(course_code: str, instructor_name: str, reviews: Iterable[Review]):
    """Return chat messages for the LLM request."""
    bullets = []
    for review in reviews:
        text = (review.text or "").strip()
        if not text:
            continue

        truncated_text = text[:MAX_REVIEW_CHARS]
        bullets.append(
            f"- Ratings (instructor {review.instructor_rating}/5, enjoyability {review.enjoyability}/5, recommend {review.recommendability}/5, difficulty {review.difficulty}/5): {truncated_text}"
        )

    joined = "\n".join(bullets)
    user_prompt = (
        f"Course: {course_code}\n"
        f"Instructor: {instructor_name}\n\n"
        "Write a concise 4-6 sentence summary of student reviews. Capture overall sentiment, teaching style, difficulty and workload patterns, and actionable advice for future students. "
        "Be neutral, specific, and avoid hedging. If themes conflict, state both. Do not invent details.\n\n"
        f"Reviews:\n{joined}"
    )

    return [
        {
            "role": "system",
            "content": (
                "You summarize university course reviews into clear, honest guidance. "
                "Do not preface the summary with headings, labels, or restating the course/instructor; "
                "just provide the summary sentences. Keep it 4-6 sentences."
            ),
        },
        {"role": "user", "content": user_prompt},
    ]


def _call_openrouter(model_name: str, messages):
    headers = {
        "Authorization": f"Bearer {getattr(settings, 'OPENROUTER_API_KEY', '')}",
        "Content-Type": "application/json",
        # OpenRouter recommends these headers for usage attribution
        "HTTP-Referer": getattr(settings, "OPENROUTER_REFERER", ""),
        "Referer": getattr(settings, "OPENROUTER_REFERER", ""),
        "X-Title": getattr(settings, "OPENROUTER_TITLE", ""),
    }
    payload = {
        "model": model_name,
        "messages": messages,
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=20,
    )
    request_id = (
        response.headers.get("x-request-id")
        or response.headers.get("x-openrouter-request-id")
        or response.headers.get("x-ratelimit-request-id")
    )
    try:
        data = response.json()
    except ValueError:
        data = None

    if not response.ok:
        error_info = (data or {}).get("error") or {}
        error_msg = error_info.get("message") or response.reason or "Unknown API error"
        request_id_str = f", request_id={request_id}" if request_id else ""
        return None, f"{response.status_code}: {error_msg}{request_id_str}"

    if data is None:
        text_snippet = (response.text or "")[:300].replace("\n", " ").strip()
        details = f"status {response.status_code}"
        if request_id:
            details += f", request_id={request_id}"
        if text_snippet:
            details += f", body='{text_snippet}'"
        return None, f"Invalid JSON response from OpenRouter ({details})."
    choices = data.get("choices") or []
    content = ""
    if choices:
        first = choices[0] or {}
        content = (
            first.get("message", {}).get("content")
            or first.get("text")
            or ""
        ).strip()
    if content:
        return content, None

    error_info = data.get("error") or {}
    error_msg = error_info.get("message") or "Received empty summary from OpenRouter."
    keys = sorted(data.keys()) if isinstance(data, dict) else []
    details = f"status {response.status_code}"
    if request_id:
        details += f", request_id={request_id}"
    if keys:
        details += f", response_keys={keys}"
    return None, f"{error_msg} ({details})."


def generate_review_summary(
    course, instructor, reviews_qs, max_reviews: int = MAX_REVIEWS_FOR_PROMPT
) -> Tuple[str | None, str | None, str | None]:
    """Call OpenRouter to create a summary. Returns (summary, error, model_used)."""

    api_key = getattr(settings, "OPENROUTER_API_KEY", "")
    if not api_key:
        return None, "OpenRouter API key is missing.", None

    max_reviews = max(1, min(max_reviews or MAX_REVIEWS_FOR_PROMPT, MAX_REVIEWS_FOR_PROMPT))
    reviews = list(
        reviews_qs.order_by("-created")[:max_reviews]
    )  # Most recent first
    reviews = [r for r in reviews if (r.text or "").strip()]
    if not reviews:
        return None, "No reviews with text to summarize.", None

    messages = _build_prompt(course.code(), instructor.full_name, reviews)

    model_name = getattr(settings, "OPENROUTER_MODEL", "openrouter/auto")
    try:
        content, error = _call_openrouter(model_name, messages)
        if content:
            return content, None, model_name
        return None, error, model_name
    except Exception as exc:  # pylint: disable=broad-except
        return None, str(exc), model_name
