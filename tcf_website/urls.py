# pylint: disable=line-too-long
"""Routes URLs to views"""

from django.urls import include, path

from . import views

urlpatterns = [
    path(
        "club-category/<str:category_slug>/",
        views.club_category,
        name="club_category",
    ),
    path("", views.index, name="index"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("privacy/", views.privacy, name="privacy"),
    path("terms/", views.terms, name="terms"),
    path("browse/", views.browse, name="browse"),
    path("department/<int:dept_id>/", views.department, name="department"),
    path(
        "department/<int:dept_id>/<str:course_recency>/",
        views.department,
        name="department_course_recency",
    ),
    path(
        "course/<int:course_id>/",
        views.course_view_legacy,
        name="course_legacy",
    ),
    path(
        "course/<int:course_id>/<int:instructor_id>/",
        views.course_instructor,
        name="course_instructor",
    ),
    path(
        "course/<int:course_id>/<int:instructor_id>/sort=<str:method>",
        views.course_instructor,
        name="sort_reviews",
    ),
    path(
        "course/<str:mnemonic>/<int:course_number>/",
        views.course_view,
        name="course",
    ),
    path(
        "course/<str:mnemonic>/<int:course_number>/<str:instructor_recency>",
        views.course_view,
        name="course_recency",
    ),
    path(
        "instructor/<int:instructor_id>/",
        views.instructor_view,
        name="instructor",
    ),
    path("reviews/new/", views.new_review, name="new_review"),
    path(
        "reviews/<int:pk>/delete/",
        views.DeleteReview.as_view(),
        name="delete_review",
    ),
    path("reviews/<int:review_id>/edit/", views.edit_review, name="edit_review"),
    path("reviews/", views.reviews, name="reviews"),
    path("reviews/<int:review_id>/upvote/", views.upvote),
    path("reviews/<int:review_id>/downvote/", views.downvote),
    path("reviews/check_duplicate/", views.review.check_duplicate),
    path(
        "reviews/check_zero_hours_per_week/",
        views.review.check_zero_hours_per_week,
    ),
    path("profile/", views.profile, name="profile"),
    path(
        "profile/<int:pk>/delete/",
        views.DeleteProfile.as_view(),
        name="delete_profile",
    ),
    path("search/", views.search, name="search"),
    # SCHEDULE URLs
    path("schedule/", views.view_schedules, name="schedule"),
    path("schedule/new/", views.new_schedule, name="new_schedule"),
    path("schedule/delete/", views.delete_schedule, name="delete_schedule"),
    path("schedule/edit/", views.edit_schedule, name="edit_schedule"),
    path(
        "schedule/duplicate/<int:schedule_id>/",
        views.duplicate_schedule,
        name="duplicate_schedule",
    ),
    path("schedule/modal/editor", views.modal_load_editor, name="modal_load_editor"),
    path(
        "schedule/modal/sections/",
        views.modal_load_sections,
        name="modal_load_sections",
    ),
    path(
        "schedule/modal/<str:mode>/",
        views.view_select_schedules_modal,
        name="modal_load_schedules",
    ),
    path("schedule/add_course/", views.schedule_add_course, name="schedule_add_course"),
    # QA URLs
    path("qa/", views.qa_dashboard, name="qa"),
    path("answers/check_duplicate/", views.qa.check_duplicate),
    path("qa/new_question/", views.new_question, name="new_question"),
    path("qa/new_answer/", views.new_answer, name="new_answer"),
    path("questions/<int:question_id>/upvote/", views.upvote_question),
    path("questions/<int:question_id>/downvote/", views.downvote_question),
    path(
        "questions/<int:pk>/delete/",
        views.DeleteQuestion.as_view(),
        name="delete_question",
    ),
    path(
        "questions/<int:question_id>/edit/",
        views.edit_question,
        name="edit_question",
    ),
    path("answers/<int:answer_id>/upvote/", views.upvote_answer),
    path("answers/<int:answer_id>/downvote/", views.downvote_answer),
    path(
        "answers/<int:pk>/delete/",
        views.DeleteAnswer.as_view(),
        name="delete_answer",
    ),
    path("answers/<int:answer_id>/edit/", views.edit_answer, name="edit_answer"),
    # API URLs
    path("api/", include("tcf_website.api.urls"), name="api"),
    # AUTH URLS
    path("login/", views.auth.login, name="login"),
    path("cognito-callback/", views.auth.cognito_callback, name="cognito_callback"),
    path("logout/", views.auth.logout, name="logout"),
]
