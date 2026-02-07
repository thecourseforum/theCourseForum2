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


def index_v2(request):
    """
    V2 Index view - New modern design.
    """
    # Load team info for the landing page
    with open("tcf_website/views/team_info.json", encoding="UTF-8") as data_file:
        team_info = json.load(data_file)

    mode = request.GET.get("mode", "courses")
    is_club = mode == "clubs"
    
    context = {
        "executive_team": team_info["executive_team"],
        "mode": mode,
        "mode_noun": "club" if is_club else "course",
        "search_placeholder": "Search for a club..." if is_club else "Search for a course or professor...",
    }

    return render(
        request,
        "v2/pages/landing.html",
        context,
    )


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


class AboutViewV2(TemplateView):
    """V2 About view - modern design."""

    template_name = "v2/pages/about.html"

    with open("tcf_website/views/team_info.json", encoding="UTF-8") as data_file:
        team_info = json.load(data_file)

    with open("tcf_website/views/team_alums.json", encoding="UTF-8") as data_file:
        alum_info = json.load(data_file)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Combine all team members into a single list
        team = []
        for member in self.team_info.get("executive_team", []):
            team.append({"name": member.get("name", ""), "role": member.get("role", "Executive"), "first_name": member.get("name", "").split()[0] if member.get("name") else "", "last_name": member.get("name", "").split()[-1] if member.get("name") else ""})
        for member in self.team_info.get("engineering_team", []):
            team.append({"name": member.get("name", ""), "role": "Engineering", "first_name": member.get("name", "").split()[0] if member.get("name") else "", "last_name": member.get("name", "").split()[-1] if member.get("name") else ""})
        for member in self.team_info.get("design_team", []):
            team.append({"name": member.get("name", ""), "role": "Design", "first_name": member.get("name", "").split()[0] if member.get("name") else "", "last_name": member.get("name", "").split()[-1] if member.get("name") else ""})
        for member in self.team_info.get("marketing_team", []):
            team.append({"name": member.get("name", ""), "role": "Marketing", "first_name": member.get("name", "").split()[0] if member.get("name") else "", "last_name": member.get("name", "").split()[-1] if member.get("name") else ""})
        context["team"] = team
        context["contributors"] = self.alum_info.get("contributors", [])
        return context
