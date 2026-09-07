"""Review upvote/downvote JSON endpoints."""

from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from ...models import Review


def _vote_response_payload(review: Review, user) -> dict[str, int]:
    """Return vote state payload for frontend updates."""
    agg = review.vote_set.aggregate(
        sum_votes=Coalesce(Sum("value"), 0),
        user_vote=Coalesce(Sum("value", filter=Q(user=user)), 0),
    )
    return {"ok": True, "sum_votes": agg["sum_votes"], "user_vote": agg["user_vote"]}


@login_required
@require_POST
def upvote(request, review_id):
    """Upvote a view."""
    review = get_object_or_404(Review, pk=review_id)
    review.upvote(request.user)
    return JsonResponse(_vote_response_payload(review, request.user))


@login_required
@require_POST
def downvote(request, review_id):
    """Downvote a view."""
    review = get_object_or_404(Review, pk=review_id)
    review.downvote(request.user)
    return JsonResponse(_vote_response_payload(review, request.user))


@login_required
@require_POST
def vote_review(request, review_id):
    """Vote on a review using a single endpoint."""
    review = get_object_or_404(Review, pk=review_id)
    action = request.POST.get("action")

    if action == "up":
        review.upvote(request.user)
    elif action == "down":
        review.downvote(request.user)
    else:
        return JsonResponse({"ok": False, "error": "Invalid action"}, status=400)

    return JsonResponse(_vote_response_payload(review, request.user))
