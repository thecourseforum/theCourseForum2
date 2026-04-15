"""Views for index and about pages."""

import json
import logging
import time
from collections import defaultdict
from pathlib import Path

import environ
from boto3.dynamodb.conditions import Attr
from django.core.cache import cache
from django.shortcuts import render
from django.views.generic.base import TemplateView

from tcf_website.analytics_utils import get_table
from tcf_website.models import Course, Instructor

from .landing_spotlight import landing_spotlight_context

logger = logging.getLogger(__name__)
# Initialize environ
env = environ.Env()

_TCF_WEBSITE_ROOT = Path(__file__).resolve().parent.parent.parent
_ABOUT_DATA_DIR = _TCF_WEBSITE_ROOT / "data" / "about"


def scan_table_paginated(filter_prefix):
    """Safely scan DynamoDB with pagination and TTL filtering."""
    # 1. Initialize the table locally (Thread-safe)
    table = get_table()
    if table is None:
        return []

    current_time, items = int(time.time()), []

    try:
        # 2. Use 'table' instead of '_TABLE'
        response = table.scan(FilterExpression=Attr("pk").begins_with(filter_prefix))

        items.extend(
            [
                i
                for i in response.get("Items", [])
                if int(i.get("expires_at", 0)) > current_time
            ]
        )

        while "LastEvaluatedKey" in response:
            # 3. Use 'table' here as well
            response = table.scan(
                FilterExpression=Attr("pk").begins_with(filter_prefix),
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(
                [
                    i
                    for i in response.get("Items", [])
                    if int(i.get("expires_at", 0)) > current_time
                ]
            )

        return items
    except Exception as e:
        logger.error(f"Error scanning DynamoDB for prefix {filter_prefix}: {e}")
        return []


def get_trending_courses():
    """Get trending courses based on DynamoDB analytics, with caching."""
    cached = cache.get("trending_courses")
    if cached is not None:
        return cached

    items = scan_table_paginated("course:")
    if not items:
        return []

    # Use a dictionary to sum up views by ID (pk) across all days
    totals = defaultdict(int)
    for item in items:
        totals[item["pk"]] += int(item.get("view_count", 0))

    # Sort the summed totals and pick the top 5 unique course IDs
    top_pks = sorted(totals.keys(), key=lambda k: totals[k], reverse=True)[:5]
    course_ids = [int(pk.split(":")[1]) for pk in top_pks]

    if not course_ids:
        return []

    # Exclude missing numbers to prevent frontend 500 erorrs
    courses = list(
        Course.objects.filter(id__in=course_ids)
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

    items = scan_table_paginated("instructor:")
    if not items:
        return []

    # FIX: Aggregate views across the TTL window so one instructor doesn't take 5 spots
    totals = defaultdict(int)
    for item in items:
        totals[item["pk"]] += int(item.get("view_count", 0))

    # Sort the summed totals
    top_pks = sorted(totals.keys(), key=lambda k: totals[k], reverse=True)[:5]
    instructor_ids = [int(pk.split(":")[1]) for pk in top_pks]

    if not instructor_ids:
        return []

    # Exclude missing names to prevent frontend 500 errors
    instructors = list(
        Instructor.objects.filter(id__in=instructor_ids)
        .exclude(first_name="")
        .exclude(last_name="")
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
