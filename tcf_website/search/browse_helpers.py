"""Browse page partial detection and advanced-search results payload."""

from ..forms import AdvancedSearchForm
from ..pagination import paginate
from .advanced import execute_advanced_search
from .course_display import course_to_row_dict, group_by_dept


def is_browse_results_partial_request(request) -> bool:
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        and request.GET.get("partial") == "results"
    )


def advanced_search_results_payload(request, form: AdvancedSearchForm) -> dict:
    """Run advanced search for a bound valid form with search params."""
    results = execute_advanced_search(form.cleaned_data)
    page_obj = paginate(results, request.GET.get("page", 1), per_page=15)
    total = page_obj.paginator.count
    courses = [course_to_row_dict(c) for c in page_obj]
    grouped = group_by_dept(courses)
    return {
        "grouped": grouped,
        "page_obj": page_obj,
        "total": total,
    }
