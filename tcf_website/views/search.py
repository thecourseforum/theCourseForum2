"""Views for search results."""

import re
import statistics
from typing import Iterable

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import F, FloatField, Value
from django.db.models.functions import Greatest, Round
from django.http import HttpResponse
from django.shortcuts import redirect, render

from ..models import Club, Instructor, Subdepartment
from ..utils import browsable_course_queryset, paginate, parse_mode

# --- Constants ----------------------------------------------------------------

# CS1110 → CS 1110 for combined_mnemonic_number trigram matching
_MNEMONIC_PATTERN = re.compile(r"^([A-Za-z]{1,4})(\d{4})$")

_SIMILARITY_THRESHOLD = 0.15
_INSTRUCTOR_SIMILARITY_THRESHOLD = 0.5

_AUTOCOMPLETE_TEMPLATE = "site/components/_autocomplete_dropdown.html"
_SEARCH_RESULTS_TEMPLATE = "site/pages/search.html"

_AUTOCOMPLETE_COURSE_LIMIT = 5
_AUTOCOMPLETE_INSTRUCTOR_LIMIT = 3
_AUTOCOMPLETE_CLUB_LIMIT = 5

_SEARCH_PAGE_SIZE = 15
_QUERY_DISPLAY_MAX_LEN = 30


# --- Query normalization -------------------------------------------------------


def normalize_search_query(raw: str) -> str:
    """Insert a space between mnemonic and number if missing, to match the index pattern."""
    match = _MNEMONIC_PATTERN.match(raw)
    return f"{match.group(1)} {match.group(2)}" if match else raw


# --- Fetchers (trigram similarity) ---------------------------------------------


def fetch_courses(query: str):
    """Course queryset ordered by similarity to the search string."""
    search_query = normalize_search_query(query)
    return (
        browsable_course_queryset()
        .annotate(
            mnemonic_similarity=TrigramSimilarity("combined_mnemonic_number", search_query),
            title_similarity=TrigramSimilarity("title", search_query),
        )
        .annotate(
            max_similarity=Round(
                Greatest(F("mnemonic_similarity"), F("title_similarity")), 2
            )
        )
        .filter(max_similarity__gte=_SIMILARITY_THRESHOLD)
        .order_by("-max_similarity")
    )


def fetch_instructors(query: str) -> list[dict]:
    """Instructor dicts with similarity scores, capped for autocomplete-scale use upstream."""
    results = (
        Instructor.objects.only("first_name", "last_name", "email")
        .annotate(
            similarity_first=TrigramSimilarity("first_name", query),
            similarity_last=TrigramSimilarity("last_name", query),
            similarity_full=TrigramSimilarity("full_name", query),
        )
        .annotate(
            max_similarity=Greatest(
                F("similarity_first"),
                F("similarity_last"),
                F("similarity_full"),
                output_field=FloatField(),
            )
        )
        .filter(max_similarity__gte=_INSTRUCTOR_SIMILARITY_THRESHOLD)
        .order_by("-max_similarity")[:10]
    )
    keys = ("first_name", "last_name", "email", "id", "max_similarity")
    return [{key: getattr(instructor, key) for key in keys} for instructor in results]


def fetch_clubs(query: str) -> list[dict]:
    """Club dicts; empty query returns all clubs ordered arbitrarily by the queryset."""
    category_annotations = {
        "category_slug": F("category__slug"),
        "category_name": F("category__name"),
    }
    base_fields = ("id", "name", "description", "max_similarity", "category_slug", "category_name")

    if not query:
        return list(
            Club.objects.annotate(
                max_similarity=Value(1.0, output_field=FloatField()),
                **category_annotations,
            ).values(*base_fields)
        )

    return [
        {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "max_similarity": c.max_similarity,
            "category_slug": c.category_slug,
            "category_name": c.category_name,
        }
        for c in Club.objects.annotate(max_similarity=TrigramSimilarity("combined_name", query))
        .filter(max_similarity__gte=_SIMILARITY_THRESHOLD)
        .annotate(**category_annotations)
        .order_by("-max_similarity")
    ]


# --- Grouping & ordering -------------------------------------------------------


def decide_order(courses: list[dict], instructors: list[dict]) -> bool:
    """Return True if courses should be listed before instructors."""

    def mean(scores: Iterable[float]) -> float:
        return statistics.mean(_scores) if (_scores := list(scores)) else 0

    courses_avg = mean(course["max_similarity"] for course in courses)
    instructors_avg = mean(instructor["max_similarity"] for instructor in instructors)
    return courses_avg > instructors_avg or not instructors


def group_by_dept(courses: list[dict]) -> dict:
    """Group courses by department mnemonic; one Subdepartment query for labels."""
    mnemonics = {course["mnemonic"] for course in courses}
    subdepts = {
        s.mnemonic: s
        for s in Subdepartment.objects.filter(mnemonic__in=mnemonics).only(
            "mnemonic", "name", "department_id"
        )
    }
    grouped: dict = {}
    for course in courses:
        mnemonic = course["mnemonic"]
        if mnemonic not in grouped:
            subdept = subdepts[mnemonic]
            grouped[mnemonic] = {
                "subdept_name": subdept.name,
                "dept_id": subdept.department_id,
                "courses": [],
            }
        grouped[mnemonic]["courses"].append(course)
    return grouped


def group_by_club_category(clubs: list[dict]) -> dict:
    """Group clubs by category slug."""
    grouped: dict = {}
    for club in clubs:
        slug = club["category_slug"]
        if slug not in grouped:
            grouped[slug] = {
                "category_name": club["category_name"],
                "category_slug": slug,
                "clubs": [],
            }
        grouped[slug]["clubs"].append(club)
    return grouped


# --- Serialization -------------------------------------------------------------


def course_to_row_dict(course, *, include_similarity: bool = False) -> dict:
    """Build a course dict for grouping/templates; search adds trigram score when present."""
    row = {
        "id": course.id,
        "title": course.title,
        "number": course.number,
        "mnemonic": course.mnemonic,
        "description": course.description,
    }
    if include_similarity:
        row["max_similarity"] = course.max_similarity
    return row


def _serialize_courses(qs) -> list[dict]:
    """Serialize a similarity-annotated course queryset for search results."""
    return [course_to_row_dict(c, include_similarity=True) for c in qs]


# --- View helpers --------------------------------------------------------------


def _autocomplete_params(request) -> dict:
    """GET params passed through for schedule/review search bar variants."""
    return {
        "autocomplete_action": request.GET.get("autocomplete_action"),
        "autocomplete_target": request.GET.get("autocomplete_target"),
    }


def _render_autocomplete(request, mode: str, is_club: bool, **context) -> HttpResponse:
    """Render the shared autocomplete dropdown partial."""
    payload = {"mode": mode, "is_club": is_club, **_autocomplete_params(request)}
    payload.update(context)
    return render(request, _AUTOCOMPLETE_TEMPLATE, payload)


def _truncate_query_display(query: str) -> str:
    """Shorten long queries for the results page heading."""
    if len(query) <= _QUERY_DISPLAY_MAX_LEN:
        return query
    return query[:_QUERY_DISPLAY_MAX_LEN] + "..."


def search(request):
    """Search results view (full page and XHR autocomplete)."""
    query = request.GET.get("q", "").strip()
    mode, is_club = parse_mode(request)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    courses_first = True
    instructors: list[dict] = []

    if is_club:
        if is_ajax:
            clubs = fetch_clubs(query)[:_AUTOCOMPLETE_CLUB_LIMIT]
            return _render_autocomplete(
                request,
                mode,
                is_club,
                courses=[],
                instructors=[],
                clubs=clubs,
                courses_first=True,
            )
        page_obj = paginate(fetch_clubs(query), request.GET.get("page", 1))
        total = page_obj.paginator.count
        grouped = group_by_club_category(page_obj)
    else:
        if not query:
            return redirect("browse")

        if is_ajax:
            courses = _serialize_courses(fetch_courses(query)[:_AUTOCOMPLETE_COURSE_LIMIT])
            instructors = fetch_instructors(query)[:_AUTOCOMPLETE_INSTRUCTOR_LIMIT]
            return _render_autocomplete(
                request,
                mode,
                is_club,
                courses=courses,
                instructors=instructors,
                courses_first=decide_order(courses, instructors),
            )

        instructors = fetch_instructors(query)
        page_obj = paginate(
            fetch_courses(query), request.GET.get("page", 1), per_page=_SEARCH_PAGE_SIZE
        )
        total = page_obj.paginator.count
        courses = _serialize_courses(page_obj)
        courses_first = decide_order(courses, instructors) if not request.GET.get("page") else True
        grouped = group_by_dept(courses)

    return render(
        request,
        _SEARCH_RESULTS_TEMPLATE,
        {
            "mode": mode,
            "is_club": is_club,
            "query": _truncate_query_display(query),
            "courses_first": courses_first,
            "grouped": grouped,
            "instructors": instructors,
            "total": total,
            "page_obj": page_obj,
        },
    )
