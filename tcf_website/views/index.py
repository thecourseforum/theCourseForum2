"""Views for index and about pages."""

import json

from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic.base import TemplateView


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
    response = render(
        request,
        "landing/landing.html",
        {
            "executive_team": team_info["executive_team"],
            "FAQs": faqs,
        },
    )
    return response


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
