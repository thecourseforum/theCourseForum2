"""Views for index and about pages."""

import json
import logging
import time
from pathlib import Path

from boto3.dynamodb.conditions import Attr, Key
from django.core.cache import cache
from django.shortcuts import render
from django.views.generic.base import TemplateView

from tcf_website.analytics_utils import get_table
from tcf_website.models import Course, Instructor

from .landing_spotlight import landing_spotlight_context

logger = logging.getLogger(__name__)

_TCF_WEBSITE_ROOT = Path(__file__).resolve().parent.parent.parent
_ABOUT_DATA_DIR = _TCF_WEBSITE_ROOT / "data" / "about"


def get_top_trending_ids(entity_type: str, count: int = 5) -> list[int]:
    """
    Query DynamoDB GSI to retrieve the most viewed entities
    Given a entity type (course or instructor) to query & the number of views
    Return the list we will display
    """
    # Initialize the table locally (Thread-safe)
    table = get_table()
    if not table:
        return []

    current_time = int(time.time())
    unique_ids = []  # To track unique entity IDs and prevent duplicates
    seen = set()  # Track seen entity_ids to avoid duplicates
    exclusive_start_key = None

    # To prevent infinite loops if the database is filled with bad data
    pages = 0
    max_pages = 10

    try:
        while len(unique_ids) < count and pages < max_pages:
            pages += 1
            query_kwargs = {
                "IndexName": "EntityIndex",
                "KeyConditionExpression": Key("entity_type").eq(entity_type),
                "FilterExpression": Attr("expires_at").gt(current_time),
                "ProjectionExpression": "pk, expires_at",
                "ScanIndexForward": False,  # Sort by highest viewed first
                "Limit": 20,
            }
            if exclusive_start_key:
                query_kwargs["ExclusiveStartKey"] = exclusive_start_key

            response = table.query(**query_kwargs)
            items = response.get("Items", [])

            # if empty early exit
            if not items:
                break

            for item in items:
                pk = item.get("pk", "")
                if ":" not in pk:
                    continue  # Skip malformed PKs
                try:
                    _, entity_id_str = pk.split(":", 1)
                    entity_id = int(entity_id_str)
                except ValueError as e:
                    logger.warning(f"Malformed pk in trending data '{pk}': {e}")
                    continue

                if entity_id not in seen:
                    unique_ids.append(entity_id)
                    seen.add(entity_id)
                if len(unique_ids) >= count:
                    break

            exclusive_start_key = response.get("LastEvaluatedKey")
            if not exclusive_start_key:
                break  # No more data to paginate through

        logger.debug(
            f"Retrieved {len(unique_ids)} trending IDs for {entity_type} in {pages} pages."
        )
        return unique_ids
    except Exception as e:
        logger.error(f"GSI query failed for {entity_type}: {e}", exc_info=True)
        return []


def get_trending_courses():
    """Get trending courses based on DynamoDB analytics, with caching."""
    cached = cache.get("trending_courses")
    if cached is not None:
        return cached

    course_ids = get_top_trending_ids("course")
    if not course_ids:
        return []

    # Source of truth lookup
    courses = list(
        Course.objects.filter(id__in=course_ids)
        .select_related("subdepartment")
        .exclude(subdepartment__mnemonic="")
        .exclude(number__isnull=True)
    )

    # preserve ranking order
    courses.sort(key=lambda c: course_ids.index(c.id))

    # set 24 hour cache
    cache.set("trending_courses", courses, timeout=24 * 60 * 60)
    return courses


def get_trending_instructors():
    """Get trending instructors based on DynamoDB analytics, with caching and aggregation."""
    cached = cache.get("trending_instructors")
    if cached is not None:
        return cached

    instructor_ids = get_top_trending_ids("instructor")
    if not instructor_ids:
        return []

    instructors = list(
        Instructor.objects.filter(id__in=instructor_ids, hidden=False).exclude(
            full_name=""
        )
    )

    # preserve ranking order
    instructors.sort(key=lambda i: instructor_ids.index(i.id))

    # set 24 hour cache
    cache.set("trending_instructors", instructors, timeout=24 * 60 * 60)
    return instructors


def index(request):
    """Index view."""
    with open(_ABOUT_DATA_DIR / "team_info.json", encoding="UTF-8") as data_file:
        team_info = json.load(data_file)

    mode = request.GET.get("mode", "courses")
    is_club = mode == "clubs"

    # Put stats onto dashboard & add to response
    trending_courses = get_trending_courses()
    trending_instructors = get_trending_instructors()

    context = {
        "executive_team": team_info["executive_team"],
        "mode": mode,
        "mode_noun": "club" if is_club else "course",
        "search_placeholder": (
            "Search for a club..." if is_club else "Search for a course or professor..."
        ),
        "trending_courses": trending_courses,
        "trending_instructors": trending_instructors,
    }
    context.update(landing_spotlight_context(mode))

    return render(
        request,
        "site/home/landing.html",
        context,
    )


def privacy(request):
    """Privacy view."""
    return render(request, "site/home/privacy.html")


def terms(request):
    """Terms view."""
    return render(request, "site/home/terms.html")


class AboutView(TemplateView):
    """About view."""

    template_name = "site/home/about.html"

    with open(_ABOUT_DATA_DIR / "team_info.json", encoding="UTF-8") as data_file:
        team_info = json.load(data_file)

    with open(_ABOUT_DATA_DIR / "team_alums.json", encoding="UTF-8") as data_file:
        alum_info = json.load(data_file)

    @staticmethod
    def _normalize_member(member: dict, fallback_role: str = "") -> dict:
        """Normalize member fields for template rendering."""
        name = member.get("name", "").strip()
        parts = name.split()
        first_name = parts[0] if parts else ""
        last_name = parts[-1] if len(parts) > 1 else ""
        initials = (
            f"{first_name[:1]}{last_name[:1]}".upper()
            if first_name and last_name
            else (first_name[:2] if first_name else "TC").upper()
        )
        return {
            "name": name,
            "first_name": first_name,
            "last_name": last_name,
            "initials": initials,
            "role": member.get("role", fallback_role),
            "class": member.get("class", ""),
            "img_filename": member.get("img_filename", ""),
            "github": member.get("github", ""),
        }

    def _normalize_members(
        self, members: list[dict], fallback_role: str = ""
    ) -> list[dict]:
        """Normalize a list of members for shared card rendering."""
        return [
            self._normalize_member(member, fallback_role=fallback_role)
            for member in members
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        executive_team = self._normalize_members(
            self.team_info.get("executive_team", [])
        )
        engineering_team = self._normalize_members(
            self.team_info.get("engineering_team", [])
        )
        design_team = self._normalize_members(self.team_info.get("design_team", []))
        marketing_team = self._normalize_members(
            self.team_info.get("marketing_team", [])
        )

        contributors = []
        for group in self.alum_info.get("contributors", []):
            contributors.append(
                {
                    "group_name": group.get("group_name", ""),
                    "members": self._normalize_members(group.get("members", [])),
                }
            )

        context["executive_team"] = executive_team
        context["engineering_team"] = engineering_team
        context["design_team"] = design_team
        context["marketing_team"] = marketing_team
        context["team"] = (
            executive_team + engineering_team + design_team + marketing_team
        )
        context["founders"] = self._normalize_members(
            self.alum_info.get("founders", [])
        )
        context["contributors"] = contributors
        return context
