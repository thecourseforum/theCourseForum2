"""Application views."""

# See
# https://docs.djangoproject.com/en/3.0/topics/db/models/#organizing-models-in-a-package

from .ads import ads
from .auth import collect_extra_info, login, login_error, logout, password_error
from .browse import (
    browse,
    course_instructor,
    course_view,
    course_view_legacy,
    department,
    instructor_view,
)
from .discord import post_message
from .index import AboutView, index, privacy, terms
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
from .review import DeleteReview, downvote, edit_review, new_review, upvote
from .search import search
