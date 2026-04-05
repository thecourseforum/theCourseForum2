"""Browse, search, and department catalog views."""

from .browse import browse
from .department import department
from .search import (
    course_to_row_dict,
    decide_order,
    fetch_clubs,
    fetch_courses,
    fetch_instructors,
    group_by_club_category,
    group_by_dept,
    normalize_search_query,
    search,
)

__all__ = [
    "browse",
    "course_to_row_dict",
    "decide_order",
    "department",
    "fetch_clubs",
    "fetch_courses",
    "fetch_instructors",
    "group_by_club_category",
    "group_by_dept",
    "normalize_search_query",
    "search",
]
