"""Views for index and about pages."""

import json
from pathlib import Path

from django.shortcuts import render
from django.views.generic.base import TemplateView

from tcf_website.utils import sis_term_code

from .landing_spotlight import landing_spotlight_context

_TCF_WEBSITE_ROOT = Path(__file__).resolve().parent.parent.parent
_ABOUT_DATA_DIR = _TCF_WEBSITE_ROOT / "data" / "about"


def index(request):
    """Index view."""
    with open(_ABOUT_DATA_DIR / "team_info.json", encoding="UTF-8") as data_file:
        team_info = json.load(data_file)

    mode = request.GET.get("mode", "courses")
    is_club = mode == "clubs"

    context = {
        "executive_team": team_info["executive_team"],
        "mode": mode,
        "mode_noun": "club" if is_club else "course",
        "search_placeholder": (
            "Search for a club..." if is_club else "Search for a course or professor..."
        ),
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


def data_snapshot(request):
    """Show the snapshot fetch_data saved for ?semester=<year>_<season>."""
    semester = request.GET.get("semester", "")
    term = sis_term_code(semester) if semester else None
    classes = []
    page_count = None
    if term is not None:
        snapshot_path = _TCF_WEBSITE_ROOT.parent / "fetched" / f"{term}.json"
        if snapshot_path.is_file():
            data = json.loads(snapshot_path.read_text(encoding="utf-8"))
            classes = data.get("classes") or []
            page_count = data.get("pageCount")
    try:
        index = int(request.GET.get("n", "0"))
    except ValueError:
        index = 0
    if classes:
        index = index % len(classes)
    section = classes[index] if classes else None
    return render(
        request,
        "site/home/snapshot.html",
        {
            "semester": semester,
            "term": term,
            "page_count": page_count,
            "section": section,
            "index": index,
            "class_count": len(classes),
        },
    )


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
