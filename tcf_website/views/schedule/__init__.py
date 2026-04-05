"""Schedule builder HTTP views (thin layer over tcf_website.schedule)."""

from .add_course_view import schedule_add_course
from .builder import view_schedules
from .crud import (
    delete_schedule,
    duplicate_schedule,
    edit_schedule,
    new_schedule,
    remove_scheduled_course,
)
from .sharing import schedule_share, schedule_unbookmark

__all__ = [
    "delete_schedule",
    "duplicate_schedule",
    "edit_schedule",
    "new_schedule",
    "remove_scheduled_course",
    "schedule_add_course",
    "schedule_share",
    "schedule_unbookmark",
    "view_schedules",
]
