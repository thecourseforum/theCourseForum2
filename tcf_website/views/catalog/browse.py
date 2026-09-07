"""Browse landing page (course catalog vs clubs) and advanced search."""

from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import render

from ...forms import AdvancedSearchForm, ClubAdvancedSearchForm
from ...models import Club, ClubCategory, School
from ...search.browse_helpers import (
    advanced_search_results_payload,
    club_advanced_search_results_payload,
    is_browse_results_partial_request,
)
from ...utils import parse_mode


def _browse_clubs(request, mode: str):
    """Clubs browse: category grid and/or filtered results."""
    club_form = ClubAdvancedSearchForm(request.GET or None)
    has_search = club_form.is_bound and club_form.has_search_params()

    if is_browse_results_partial_request(request):
        if not has_search:
            return HttpResponse(status=204)
        payload = club_advanced_search_results_payload(request, club_form)
        return render(
            request,
            "site/catalog/partials/_browse_club_advanced_results.html",
            {"request": request, **payload},
        )

    club_categories = (
        ClubCategory.objects.all()
        .prefetch_related(
            Prefetch(
                "club_set",
                queryset=Club.objects.order_by("name"),
                to_attr="clubs",
            )
        )
        .order_by("name")
    )

    if has_search:
        payload = club_advanced_search_results_payload(request, club_form)
        return render(
            request,
            "site/catalog/browse.html",
            {
                "is_club": True,
                "mode": mode,
                "club_form": club_form,
                "has_search": True,
                "club_categories": club_categories,
                **payload,
            },
        )

    return render(
        request,
        "site/catalog/browse.html",
        {
            "is_club": True,
            "mode": mode,
            "club_form": club_form if club_form.is_bound else ClubAdvancedSearchForm(),
            "has_search": False,
            "club_categories": club_categories,
        },
    )


def _browse_courses(request, mode: str):
    """Courses browse: schools grid and/or advanced search results."""
    form = AdvancedSearchForm(request.GET or None)
    has_search = form.is_bound and form.has_search_params()

    if is_browse_results_partial_request(request):
        if not has_search:
            return HttpResponse(status=204)
        payload = advanced_search_results_payload(request, form)
        return render(
            request,
            "site/catalog/partials/_browse_advanced_results.html",
            {"request": request, **payload},
        )

    if has_search:
        payload = advanced_search_results_payload(request, form)
        return render(
            request,
            "site/catalog/browse.html",
            {
                "is_club": False,
                "mode": mode,
                "form": form,
                "has_search": True,
                **payload,
            },
        )

    featured = {
        s.name: s
        for s in School.objects.filter(
            name__in=[
                "College of Arts & Sciences",
                "School of Engineering & Applied Science",
            ]
        )
    }
    clas = featured["College of Arts & Sciences"]
    seas = featured["School of Engineering & Applied Science"]

    excluded_list = [clas.pk, seas.pk]
    other_schools = School.objects.exclude(pk__in=excluded_list).order_by("name")

    return render(
        request,
        "site/catalog/browse.html",
        {
            "is_club": False,
            "mode": mode,
            "form": form if form.is_bound else AdvancedSearchForm(),
            "has_search": False,
            "CLAS": clas,
            "SEAS": seas,
            "other_schools": other_schools,
        },
    )


def browse(request):
    """View for browse page with advanced course or club search."""
    mode, is_club = parse_mode(request)
    if is_club:
        return _browse_clubs(request, mode)
    return _browse_courses(request, mode)
