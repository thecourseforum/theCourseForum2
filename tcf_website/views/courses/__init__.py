"""Course detail and course–instructor pair views."""

from .course import (
    build_section_times_maps_by_instructor,
    course_view,
    is_lecture_section,
    split_section_times,
)
from .course_instructor import course_instructor

__all__ = [
    "build_section_times_maps_by_instructor",
    "course_instructor",
    "course_view",
    "is_lecture_section",
    "split_section_times",
]
