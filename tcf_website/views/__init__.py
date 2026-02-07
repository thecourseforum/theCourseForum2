"""Application views."""

# See
# https://docs.djangoproject.com/en/3.0/topics/db/models/#organizing-models-in-a-package

from .auth import login, logout
from .browse import (
    browse,
    browse_v2,
    course_instructor,
    course_instructor_v2,
    course_view,
    course_view_legacy,
    course_view_v2,
    department,
    department_v2,
    instructor_view,
    instructor_view_v2,
    club_category,
)
from .index import AboutView, AboutViewV2, index, index_v2, privacy, terms
from .profile import DeleteProfile, profile, profile_v2, reviews
from .qa import (
    DeleteAnswer,
    DeleteQuestion,
    downvote_answer,
    downvote_question,
    edit_answer,
    edit_question,
    new_answer,
    new_question,
    upvote_answer,
    upvote_question,
)
from .review import DeleteReview, downvote, new_review, upvote, new_review_v2
from .schedule import (
    delete_schedule,
    duplicate_schedule,
    edit_schedule,
    modal_load_editor,
    modal_load_sections,
    new_schedule,
    schedule_add_course,
    view_schedules,
    view_select_schedules_modal,
)
from .search import search
