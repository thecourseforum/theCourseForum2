"""Application views."""

from .account import DeleteProfile, profile, reviews
from .auth import forgot_password, login, logout
from .catalog import browse, department, search
from .clubs import club_category, club_view
from .courses import course_instructor, course_view
from .home import AboutView, index, privacy, terms
from .instructors import instructor_view
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
    schedule_share,
    schedule_unbookmark,
    view_schedules,
)
