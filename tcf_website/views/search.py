# pylint: disable=invalid-name
"""Views for search results"""
import re
import statistics
from typing import Iterable

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import F, FloatField, Q, Value
from django.db.models.functions import Greatest, Round
from django.shortcuts import redirect, render

from ..models import Club, Course, Instructor, Subdepartment
from ..utils import paginate

# Compiled once at import time; matches patterns like "CS1110" → ("CS", "1110")
_MNEMONIC_PATTERN = re.compile(r"^([A-Za-z]{1,4})(\d{4})$")

# Minimum trigram similarity score for course/club results (instructors use a higher threshold)
_SIMILARITY_THRESHOLD = 0.15
_INSTRUCTOR_SIMILARITY_THRESHOLD = 0.5


def parse_mode(request):
    """Parse the mode parameter from the request."""
    mode = request.GET.get("mode", "courses")
    return mode, (mode == "clubs")


def normalize_search_query(q: str) -> str:
    """Add a space between mnemonic and number if missing, to match the index pattern."""
    match = _MNEMONIC_PATTERN.match(q)
    return f"{match.group(1)} {match.group(2)}" if match else q


def fetch_courses(query):
    """Get course data using Django trigram similarity."""
    search_query = normalize_search_query(query)
    return (
        Course.objects.select_related("subdepartment")
        .only("title", "number", "subdepartment__mnemonic", "description")
        .annotate(
            mnemonic_similarity=TrigramSimilarity("combined_mnemonic_number", search_query),
            title_similarity=TrigramSimilarity("title", search_query),
        )
        .annotate(
            max_similarity=Round(
                Greatest(F("mnemonic_similarity"), F("title_similarity")), 2
            )
        )
        .annotate(mnemonic=F("subdepartment__mnemonic"))
        .filter(max_similarity__gte=_SIMILARITY_THRESHOLD)
        .filter(Q(number__isnull=True) | Q(number__range=(1000, 9999)))
        .exclude(semester_last_taught_id__lt=48)
        .order_by("-max_similarity")
    )


def fetch_instructors(query) -> list[dict]:
    """Get instructor data using Django trigram similarity."""
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
    return [
        {
            key: getattr(instructor, key)
            for key in ("first_name", "last_name", "email", "id", "max_similarity")
        }
        for instructor in results
    ]


def fetch_clubs(query):
    """Get club data using Django trigram similarity."""
    if not query:
        return list(
            Club.objects.annotate(
                max_similarity=Value(1.0, output_field=FloatField()),
                category_slug=F("category__slug"),
                category_name=F("category__name"),
            ).values("id", "name", "description", "max_similarity", "category_slug", "category_name")
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
        for c in Club.objects.annotate(
            max_similarity=TrigramSimilarity("combined_name", query)
        )
        .filter(max_similarity__gte=_SIMILARITY_THRESHOLD)
        .annotate(category_slug=F("category__slug"), category_name=F("category__name"))
        .order_by("-max_similarity")
    ]


def decide_order(courses: list[dict], instructors: list[dict]) -> bool:
    """Return True if courses should be displayed before instructors."""

    def mean(scores: Iterable[float]) -> float:
        return statistics.mean(_scores) if (_scores := list(scores)) else 0

    courses_avg = mean(course["max_similarity"] for course in courses)
    instructors_avg = mean(instructor["max_similarity"] for instructor in instructors)
    return courses_avg > instructors_avg or not instructors


def group_by_dept(courses):
    """Group courses by department mnemonic, fetching subdepartment info in one query."""
    mnemonics = {course["mnemonic"] for course in courses}
    subdepts = {
        s.mnemonic: s
        for s in Subdepartment.objects.filter(mnemonic__in=mnemonics).only(
            "mnemonic", "name", "department_id"
        )
    }
    grouped = {}
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


def group_by_club_category(clubs):
    """Group clubs by category slug."""
    grouped = {}
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


def _serialize_courses(qs):
    """Serialize a course queryset to a list of dicts."""
    return [
        {
            "id": c.id,
            "title": c.title,
            "number": c.number,
            "mnemonic": c.mnemonic,
            "description": c.description,
            "max_similarity": c.max_similarity,
        }
        for c in qs
    ]


def search(request):
    """Search results view."""
    query = request.GET.get("q", "").strip()
    mode, is_club = parse_mode(request)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if is_club:
        if is_ajax:
            return render(request, "site/components/_autocomplete_dropdown.html", {
                "mode": mode,
                "is_club": is_club,
                "courses": [],
                "instructors": [],
                "courses_first": True,
                "autocomplete_action": request.GET.get("autocomplete_action"),
                "autocomplete_target": request.GET.get("autocomplete_target"),
            })
        page_obj = paginate(fetch_clubs(query), request.GET.get("page", 1))
        total = page_obj.paginator.count
        grouped = group_by_club_category(page_obj)
    else:
        if not query:
            return redirect("browse")

        if is_ajax:
            courses = _serialize_courses(fetch_courses(query)[:5])
            instructors = fetch_instructors(query)[:3]
            return render(request, "site/components/_autocomplete_dropdown.html", {
                "mode": mode,
                "is_club": is_club,
                "courses_first": decide_order(courses, instructors),
                "courses": courses,
                "instructors": instructors,
                "autocomplete_action": request.GET.get("autocomplete_action"),
                "autocomplete_target": request.GET.get("autocomplete_target"),
            })

        instructors = fetch_instructors(query)
        page_obj = paginate(fetch_courses(query), request.GET.get("page", 1), per_page=15)
        total = page_obj.paginator.count
        courses = _serialize_courses(page_obj)
        courses_first = decide_order(courses, instructors) if not request.GET.get("page") else True
        grouped = group_by_dept(courses)

    return render(request, "site/pages/search.html", {
        "mode": mode,
        "is_club": is_club,
        "query": query[:30] + ("..." if len(query) > 30 else ""),
        "courses_first": courses_first,
        "grouped": grouped,
        "instructors": instructors,
        "total": total,
        "page_obj": page_obj,
    })
