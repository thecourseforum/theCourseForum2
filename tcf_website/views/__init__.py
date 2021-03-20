"""Application views."""

# See
# https://docs.djangoproject.com/en/3.0/topics/db/models/#organizing-models-in-a-package

from .ads import ads
from .auth import login, login_error, logout, collect_extra_info
from .blog import BlogView, BlogPostView, blog_posts, post
from .browse import (browse, department, course_view_legacy, course_view,
                     course_instructor, instructor_view)
from .discord import post_message
from .index import index, privacy, terms, AboutView
from .profile import profile, reviews
from .review import new_review, DeleteReview, upvote, downvote, edit_review
from .search import search
