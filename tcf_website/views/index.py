"""Views for index and about pages."""

import json
import logging
import time

import boto3
import environ
from boto3.dynamodb.conditions import Attr
from django.core.cache import cache
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic.base import TemplateView

from tcf_website.models import Course, Instructor

logger = logging.getLogger(__name__)
# Initialize environ
env = environ.Env()

access_key = env("AWS_ANALYTICS_ACCESS_KEY_ID", default=None)
secret_key = env("AWS_ANALYTICS_SECRET_ACCESS_KEY", default=None)
table_name = env("DYNAMODB_TABLE_NAME", default="trending_analytics")
# Initialize DynamoDB session securely
if access_key and secret_key:
    try:
        _DYNAMODB = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=env("AWS_REGION", default="us-east-1"),
        ).resource("dynamodb")
        _TABLE = _DYNAMODB.Table(table_name)
    except Exception as e:
        logger.error(f"Failed to initialize DynamoDB in index.py: {e}")
        _TABLE = None
else:
    logger.info("DynamoDB analytics disabled in index.py: missing credentials")
    _TABLE = None


def index(request):
    """
    Index view.

    Redirect to landing page if user not authorized.
    """

    # Load "About Team" data from json file
    with open("tcf_website/views/team_info.json", encoding="UTF-8") as data_file:
        team_info = json.load(data_file)
    # Load FAQ data from json file, evaluating tags and filters
    rendered = render_to_string("landing/_faqs.json")
    faqs = json.loads(rendered)
    # Put stats onto dashboard & add to response
    trending_courses = get_trending_courses()
    trending_instructors = get_trending_instructors()

    response = render(
        request,
        "landing/landing.html",
        {
            "executive_team": team_info["executive_team"],
            "FAQs": faqs,
            "trending_courses": trending_courses,
            "trending_instructors": trending_instructors,
        },
    )
    return response


def scan_table_paginated(filter_prefix):
    """Helper funtion to safely scan DynamoDB with pagination, TTL filtering, and expetion handling."""
    if _TABLE is None:
        return []
    current_time = int(time.time())
    items = []

    try:
        # Initial scan
        response = _TABLE.scan(FilterExpression=Attr("pk").begins_with(filter_prefix))
        # Filter TTL ghosts immediately to save memrory
        items.extend(
            [
                i
                for i in response.get("Items", [])
                if int(i.get("expires_at", 0)) > current_time
            ]
        )
        # Paginate through results if 1MB limit
        while "LastEvaluatedKey" in response:
            response = _TABLE.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr("pk").begins_with(
                    filter_prefix
                ),
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

    # Safe sort that handles missing view counts
    top_items = sorted(items, key=lambda x: int(x.get("view_count", 0)), reverse=True)[
        :5
    ]
    course_ids = [int(item["pk"].split(":")[1]) for item in top_items]

    if not course_ids:
        return []

    # Exclude missing numbers to prevent frontend 500 erorrs
    courses = list(
        Course.objects.filter(id__in=course_ids)
        .exclude(mnemonic="")
        .exclude(number__isnull=True)
    )
    # preserve ranking order
    courses.sort(key=lambda c: course_ids.index(c.id))
    # set 24 hour cache
    cache.set("trending_courses", courses, timeout=24 * 60 * 60)
    return courses


def get_trending_instructors():
    # Explicit None Check
    """Get trending instructors based on DynamoDB analytics, with caching."""
    cached = cache.get("trending_instructors")
    if cached is not None:
        return cached

    items = scan_table_paginated("instructor:")
    if not items:
        return []

    # Safe sort that handles missing view counts
    top_items = sorted(items, key=lambda x: int(x.get("view_count", 0)), reverse=True)[
        :5
    ]
    instructor_ids = [int(item["pk"].split(":")[1]) for item in top_items]

    if not instructor_ids:
        return []

    # Exclude missing numbers to prevent frontend 500 erorrs
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


def privacy(request):
    """Privacy view."""
    return render(request, "about/privacy.html")


def terms(request):
    """Terms view."""
    return render(request, "about/terms.html")


class AboutView(TemplateView):
    """About view."""

    template_name = "about/about.html"

    # Load data from json files
    with open("tcf_website/views/team_info.json", encoding="UTF-8") as data_file:
        team_info = json.load(data_file)

    with open("tcf_website/views/team_alums.json", encoding="UTF-8") as data_file:
        alum_info = json.load(data_file)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["executive_team"] = self.team_info["executive_team"]
        context["engineering_team"] = self.team_info["engineering_team"]
        context["marketing_team"] = self.team_info["marketing_team"]
        context["design_team"] = self.team_info["design_team"]
        context["founders"] = self.alum_info["founders"]
        context["contributors"] = self.alum_info["contributors"]
        return context
