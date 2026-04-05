"""Recent reviews for the landing page spotlight section."""

from __future__ import annotations

import textwrap

from django.conf import settings
from django.db.models import Q
from django.urls import reverse

from ...models import Review
from ...utils import browsable_course_queryset, with_mode

_RECENT_REVIEWS_LIMIT = 10
_SNIPPET_WIDTH = 120


def _visible_review_q() -> Q:
    return Q(
        hidden=False,
        toxicity_rating__lt=settings.TOXICITY_THRESHOLD,
    )


def _snippet(text: str) -> str:
    cleaned = " ".join(text.split())
    return textwrap.shorten(cleaned, width=_SNIPPET_WIDTH, placeholder="…")


def _recent_course_review_rows(mode: str) -> list[dict]:
    browsable = browsable_course_queryset()
    qs = (
        Review.objects.filter(
            _visible_review_q(),
            course__in=browsable,
            instructor__isnull=False,
            club__isnull=True,
        )
        .exclude(text="")
        .only("id", "text", "course_id", "instructor_id")
        .select_related("course__subdepartment", "instructor")
        .order_by("-created")[:_RECENT_REVIEWS_LIMIT]
    )
    rows = []
    for rev in qs:
        course = rev.course
        inst = rev.instructor
        source = f"{course.code()} · {(inst.full_name or '').strip() or inst.last_name}"
        rows.append(
            {
                "text": _snippet(rev.text),
                "source": source,
                "href": with_mode(
                    reverse(
                        "course_instructor",
                        args=[rev.course_id, rev.instructor_id],
                    ),
                    mode,
                ),
            }
        )
    return rows


def _recent_club_review_rows() -> list[dict]:
    qs = (
        Review.objects.filter(
            _visible_review_q(),
            club__isnull=False,
        )
        .exclude(text="")
        .only("id", "text", "club_id")
        .select_related("club", "club__category")
        .order_by("-created")[:_RECENT_REVIEWS_LIMIT]
    )
    rows = []
    for rev in qs:
        club = rev.club
        rows.append(
            {
                "text": _snippet(rev.text),
                "source": club.name,
                "href": with_mode(
                    reverse("club", args=[club.category.slug, club.id]),
                    "clubs",
                ),
            }
        )
    return rows


def landing_spotlight_context(mode: str) -> dict:
    """Context for the landing reviews strip (list may be empty)."""
    if mode == "clubs":
        return {"landing_spotlight_reviews": _recent_club_review_rows()}
    return {"landing_spotlight_reviews": _recent_course_review_rows(mode)}
