"""Application views."""

# See
# https://docs.djangoproject.com/en/3.0/topics/db/models/#organizing-models-in-a-package

from .auth import login, login_error, logout, collect_extra_info
from .index import index, privacy, terms, AboutView
from .browse import browse, department, course_view, course_instructor, instructor_view
from .review import new_review, DeleteReview, upvote, downvote
from .profile import profile, reviews
from .search import search
from .discord import post_message
