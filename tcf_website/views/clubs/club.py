"""Club category, event, and detail views."""

import json
from calendar import Calendar
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.http import urlencode

from ...models import Club, ClubCategory, Review
from ...pagination import paginate
from ...utils import with_mode


def _get_paginated_club_reviews(club: Club, user, page_number=1, method=""):
    """Build sorted/paginated club reviews with vote annotations."""
    reviews = Review.objects.filter(
        club=club,
        toxicity_rating__lt=settings.TOXICITY_THRESHOLD,
        hidden=False,
    ).exclude(text="")

    reviews = reviews.annotate(sum_votes=Coalesce(Sum("vote__value"), Value(0)))

    if user.is_authenticated:
        reviews = reviews.annotate(
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


def _event_calendar(request, start_date, event_days, eastern):
    today = datetime.now(eastern).date()
    month = start_date.replace(day=1)
    selected = None
    try:
        requested = date.fromisoformat(request.GET.get("day", ""))
    except ValueError:
        requested = None
    if requested and 2 <= requested.year <= 9998:
        month = requested.replace(day=1)
        selected = requested

    weeks = Calendar(firstweekday=6).monthdatescalendar(month.year, month.month)
    month_days = [day for week in weeks for day in week if day.month == month.month]
    return {
        "month": month,
        "today": today,
        "previous_month": (month - timedelta(days=1)).replace(day=1),
        "next_month": month_days[-1] + timedelta(days=1),
        "selected": selected,
        "selected_events": event_days.get(selected, []),
        "count": len({event["id"] for day in month_days for event in event_days.get(day, [])}),
        "weeks": [
            [
                {"date": day, "events": event_days.get(day, [])}
                for day in week
            ]
            for week in weeks
        ],
    }


def club_events(request):
    """Render the club events page."""
    sample_path = Path(__file__).with_name("data") / "sample-data.json"
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    start_date = date.fromisoformat(sample["start_date"])
    end_date = date.fromisoformat(sample["end_date"])
    date_error = ""
    try:
        requested_start = date.fromisoformat(request.GET.get("from") or start_date.isoformat())
        requested_end = date.fromisoformat(request.GET.get("to") or end_date.isoformat())
        if requested_start > requested_end or not (
            2 <= requested_start.year <= requested_end.year <= 9998
        ):
            raise ValueError
    except ValueError:
        date_error = "Enter a valid date range with From on or before To."
    else:
        start_date, end_date = requested_start, requested_end
    eastern = ZoneInfo("America/New_York")
    event_query = request.GET.get("q", "").strip()
    search_terms = event_query.casefold().split()
    categories = {category["slug"]: category["name"] for category in sample["categories"]}
    selected_category = request.GET.get("category", "")
    if selected_category not in categories:
        selected_category = ""
    clubs = {
        club["slug"]: club["name"]
        for club in sorted(sample["clubs"], key=lambda club: club["name"].casefold())
    }
    selected_club = request.GET.get("club", "")
    if selected_club not in clubs:
        selected_club = ""
    interests = sample["interests"]
    selected_interest = request.GET.get("interest", "")
    if selected_interest not in interests:
        selected_interest = ""
    sort_options = {"soonest": "Soonest first", "latest": "Latest first", "title": "Title A-Z"}
    event_sort = request.GET.get("sort", "soonest")
    if event_sort not in sort_options:
        event_sort = "soonest"
    matching_events = []
    list_events = []
    calendar_days = {}
    for event in sample["events"]:
        if event["cancelled"] or (
            selected_category and event["category"] != categories[selected_category]
        ):
            continue
        if selected_club and clubs[selected_club] not in event["clubs"]:
            continue
        if selected_interest and selected_interest not in event["interests"]:
            continue
        search_text = " ".join(
            [event["title"], event["location"], event["category"], *event["clubs"], *event["interests"]]
        ).casefold()
        if not all(term in search_text for term in search_terms):
            continue
        for key in ("starts_at", "ends_at"):
            event[key] = datetime.fromisoformat(event[key])
            if event.get("all_day"):
                event[key] = event[key].replace(tzinfo=eastern)
            else:
                event[key] = event[key].astimezone(eastern)
        matching_events.append(event)

    matching_events.sort(key=lambda event: event["starts_at"], reverse=event_sort == "latest")
    if event_sort == "title":
        matching_events.sort(key=lambda event: event["title"].casefold())

    for event in matching_events:
        day = event["starts_at"].date()
        last_day = event["ends_at"].date()
        if not event.get("all_day") and event["ends_at"].time() == datetime.min.time():
            last_day -= timedelta(days=1)
        day = max(day, start_date)
        last_day = min(last_day, end_date)
        if day <= last_day:
            event["list_date"] = day
            list_events.append(event)
        while day <= last_day:
            calendar_days.setdefault(day, []).append(event)
            day += timedelta(days=1)

    calendar = _event_calendar(request, start_date, calendar_days, eastern)
    calendar_query = urlencode(
        {
            "mode": "clubs",
            "view": "month",
            "q": event_query,
            "category": selected_category,
            "club": selected_club,
            "interest": selected_interest,
            "sort": event_sort,
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
        }
    )
    if request.GET.get("partial") == "calendar":
        return render(
            request,
            "site/clubs/components/_event_calendar.html",
            {
                "calendar": calendar,
                "calendar_query": calendar_query,
                "is_month_view": True,
            },
        )

    return render(
        request,
        "site/clubs/club_events.html",
        {
            "start_date": start_date,
            "end_date": end_date,
            "date_error": date_error,
            "list_events": list_events,
            "event_count": len(list_events),
            "calendar": calendar,
            "calendar_query": calendar_query,
            "event_query": event_query,
            "categories": categories,
            "selected_category": selected_category,
            "clubs": clubs,
            "selected_club": selected_club,
            "interests": interests,
            "selected_interest": selected_interest,
            "sort_options": sort_options,
            "event_sort": event_sort,
            "is_month_view": request.GET.get("view") == "month",
        },
    )


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
        "site/clubs/club_category.html",
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
        "site/clubs/club.html",
        _build_club_page_context(request, club, mode),
    )
