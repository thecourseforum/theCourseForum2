"""Application views."""

# See
# https://docs.djangoproject.com/en/3.0/topics/db/models/#organizing-models-in-a-package

from .auth import login, logout
from .browse import (
    browse,
    club_category,
    course_instructor,
    course_view,
    course_view_legacy,
    department,
    instructor_view,
)
from .forum import (
    create_post,
    create_response,
    delete_post,
    delete_response,
    edit_post,
    edit_response,
    forum_dashboard,
    forum_post_detail,
    get_categories,
    search_courses,
    vote_post,
    vote_response,
)
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
    qa_dashboard,
    qa_dashboard_hard,
    question_detail,
    upvote_answer,
    upvote_question,
)
from .review import DeleteReview, downvote, edit_review, new_review, upvote
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
