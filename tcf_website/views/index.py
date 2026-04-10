"""Views for index and about pages."""

import json

import boto3
import environ
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic.base import TemplateView

from tcf_website.models import Course, Instructor

# Initialize environ
env = environ.Env()

access_key = env("AWS_ANALYTICS_ACCESS_KEY_ID", default=None)
secret_key = env("AWS_ANALYTICS_SECRET_ACCESS_KEY", default=None)
table_name = env("DYNAMODB_TABLE_NAME", default="trending_analytics")

if access_key and secret_key:
    dynamodb = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=env("AWS_REGION", default="us-east-1"),
    ).resource("dynamodb")
    table = dynamodb.Table(table_name)
else:
    table = None


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

    # put stats onto dashboard (& add to response)
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


# Functions to fetch trending courses and instructors (placeholder for now, can be replaced with real analytics data)
def get_trending_courses():
    if table is None:
        return []  # Return empty list if DynamoDB is not initialized

    # WILL Query for trending, ensures effciecny TEMP SCAN
    result = table.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr("pk").begins_with("course:")
    )

    items = sorted(result["Items"], key=lambda x: x["view_count"], reverse=True)[:5]
    course_ids = [int(item["pk"].split(":")[1]) for item in items]

    # Preserve ranking order
    courses = list(Course.objects.filter(id__in=course_ids))
    courses.sort(key=lambda c: course_ids.index(c.id))

    return courses


def get_trending_instructors():
    if table is None:
        return []  # Return empty list if DynamoDB is not initialized

    # Query for trending, ensures effciecny
    result = table.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr("pk").begins_with("instructor:")
    )

    items = sorted(result["Items"], key=lambda x: x["view_count"], reverse=True)[:5]
    instructor_ids = [int(item["pk"].split(":")[1]) for item in items]

    # Preserve ranking order
    instructors = list(Instructor.objects.filter(id__in=instructor_ids))
    instructors.sort(key=lambda i: instructor_ids.index(i.id))

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
