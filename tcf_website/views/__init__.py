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
    club_category_v2,
    club_view_v2,
)
from .index import (
    AboutView,
    AboutViewV2,
    index,
    index_v2,
    privacy,
    privacy_v2,
    terms,
    terms_v2,
)
from .profile import DeleteProfile, profile, profile_v2, reviews, reviews_v2
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
from .review import (
    DeleteReview,
    downvote,
    new_review,
    new_review_v2,
    upvote,
    vote_review,
)
from .schedule import (
    delete_schedule,
    duplicate_schedule,
    edit_schedule,
    modal_load_editor,
    modal_load_sections,
    new_schedule,
    remove_scheduled_course_v2,
    schedule_add_course,
    schedule_add_course_v2,
    view_schedules,
    view_schedules_v2,
    view_select_schedules_modal,
)
from .search import search
