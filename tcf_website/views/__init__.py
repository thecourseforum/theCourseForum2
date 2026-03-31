"""Application views."""

# See
# https://docs.djangoproject.com/en/3.0/topics/db/models/#organizing-models-in-a-package

from .auth import login, logout
from .browse import browse
from .club import club_category, club_view
from .course import course_view
from .course_instructor import course_instructor
from .department import department
from .instructor import instructor_view
from .index import (
    AboutView,
    index,
    privacy,
    terms,
)
from .profile import DeleteProfile, profile, reviews
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
    upvote,
    vote_review,
)
from .schedule import (
    delete_schedule,
    duplicate_schedule,
    edit_schedule,
    new_schedule,
    remove_scheduled_course,
    schedule_add_course,
    view_schedules,
)
from .search import search
