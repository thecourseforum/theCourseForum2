"""Club category and club detail views."""

from django.conf import settings
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from ..models import Club, ClubCategory, Review
from ..pagination import paginate
from ..utils import with_mode


def _get_paginated_club_reviews(club: Club, user, page_number=1, method=""):
    """Build sorted/paginated club reviews with vote annotations."""
    reviews = Review.objects.filter(
        club=club,
        toxicity_rating__lt=settings.TOXICITY_THRESHOLD,
        hidden=False,
    ).exclude(text="")

    if user.is_authenticated:
        reviews = reviews.annotate(
            sum_votes=Coalesce(Sum("vote__value"), Value(0)),
            user_vote=Coalesce(
                Sum("vote__value", filter=Q(vote__user=user)),
                Value(0),
            ),
        )

    return paginate(Review.sort(reviews, method), page_number)


def _build_club_page_context(request, club: Club, mode: str):
    """Build shared context for club detail pages."""
    sort_method = request.GET.get("sort", "")
    page_number = request.GET.get("page", 1)
    paginated_reviews = _get_paginated_club_reviews(
        club, request.user, page_number, sort_method
    )

    breadcrumbs = [
        ("Clubs", with_mode(reverse("browse"), "clubs"), False),
        (
            club.category.name,
            with_mode(reverse("club_category", args=[club.category.slug]), "clubs"),
            False,
        ),
        (club.name, None, True),
    ]

    return {
        "is_club": True,
        "mode": mode,
        "club": club,
        "paginated_reviews": paginated_reviews,
        "num_reviews": paginated_reviews.paginator.count,
        "sort_method": sort_method,
        "breadcrumbs": breadcrumbs,
        "course_code": f"{club.category.slug} {club.id}",
        "course_title": club.name,
    }


def club_category(request, category_slug: str):
    """View for club category page."""
    mode = "clubs"
    category = get_object_or_404(ClubCategory, slug=category_slug.upper())
    clubs = Club.objects.filter(category=category).order_by("name")

    paginated_clubs = paginate(clubs, request.GET.get("page", 1))

    breadcrumbs = [
        ("Clubs", with_mode(reverse("browse"), "clubs"), False),
        (category.name, None, True),
    ]

    return render(
        request,
        "site/pages/club_category.html",
        {
            "is_club": True,
            "mode": mode,
            "category": category,
            "paginated_clubs": paginated_clubs,
            "breadcrumbs": breadcrumbs,
        },
    )


def club_view(request, category_slug: str, club_id: int):
    """View for club detail page."""
    mode = "clubs"
    club = get_object_or_404(Club, id=club_id, category__slug=category_slug.upper())
    return render(
        request,
        "site/pages/club.html",
        _build_club_page_context(request, club, mode),
    )
