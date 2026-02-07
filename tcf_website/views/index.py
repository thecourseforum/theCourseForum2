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


def privacy_v2(request):
    """V2 Privacy view."""
    return render(request, "v2/pages/privacy.html")


def terms(request):
    """Terms view."""
    return render(request, "about/terms.html")


def terms_v2(request):
    """V2 Terms view."""
    return render(request, "v2/pages/terms.html")


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

    @staticmethod
    def _normalize_member(member: dict, fallback_role: str = "") -> dict:
        """Normalize member fields for v2 template rendering."""
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

    def _normalize_members(self, members: list[dict], fallback_role: str = "") -> list[dict]:
        """Normalize a list of members for shared card rendering."""
        return [
            self._normalize_member(member, fallback_role=fallback_role)
            for member in members
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        executive_team = self._normalize_members(self.team_info.get("executive_team", []))
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
        context["team"] = executive_team + engineering_team + design_team + marketing_team
        context["founders"] = self._normalize_members(self.alum_info.get("founders", []))
        context["contributors"] = contributors
        return context
