# pylint: disable=line-too-long
"""Routes URLs to views"""

from django.urls import path

from . import views

urlpatterns = [
    path(
        "club-category/<str:category_slug>/",
        views.club_category,
        name="club_category",
    ),
    path(
        "v2/club-category/<str:category_slug>/",
        views.club_category_v2,
        name="club_category_v2",
    ),
    path(
        "v2/club/<str:category_slug>/<int:club_id>/",
        views.club_view_v2,
        name="club_v2",
    ),
    path("", views.index, name="index"),
    path("v2/", views.index_v2, name="index_v2"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("v2/about/", views.AboutViewV2.as_view(), name="about_v2"),
    path("privacy/", views.privacy, name="privacy"),
    path("terms/", views.terms, name="terms"),
    path("browse/", views.browse, name="browse"),
    path("v2/browse/", views.browse_v2, name="browse_v2"),
    path("department/<int:dept_id>/", views.department, name="department"),
    path(
        "department/<int:dept_id>/<str:course_recency>/",
        views.department,
        name="department_course_recency",
    ),
    path("v2/department/<int:dept_id>/", views.department_v2, name="department_v2"),
    path(
        "v2/department/<int:dept_id>/<str:course_recency>/",
        views.department_v2,
        name="department_v2_course_recency",
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
        "v2/course/<int:course_id>/<int:instructor_id>/",
        views.course_instructor_v2,
        name="course_instructor_v2",
    ),
    path(
        "v2/course/<int:course_id>/<int:instructor_id>/sort=<str:method>",
        views.course_instructor_v2,
        name="sort_reviews_v2",
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
        "v2/course/<str:mnemonic>/<int:course_number>/",
        views.course_view_v2,
        name="course_v2",
    ),
    path(
        "instructor/<int:instructor_id>/",
        views.instructor_view,
        name="instructor",
    ),
    path(
        "v2/instructor/<int:instructor_id>/",
        views.instructor_view_v2,
        name="instructor_v2",
    ),
    path("reviews/new/", views.new_review, name="new_review"),
    path("v2/reviews/new/", views.new_review_v2, name="new_review_v2"),
    path(
        "reviews/<int:pk>/delete/",
        views.DeleteReview.as_view(),
        name="delete_review",
    ),
    path("reviews/", views.reviews, name="reviews"),
    path("v2/reviews/", views.reviews_v2, name="reviews_v2"),
    path("reviews/<int:review_id>/upvote/", views.upvote),
    path("reviews/<int:review_id>/downvote/", views.downvote),
    path("reviews/<int:review_id>/vote/", views.vote_review, name="vote_review"),
    path("reviews/check_duplicate/", views.review.check_duplicate),
    path(
        "reviews/check_zero_hours_per_week/",
        views.review.check_zero_hours_per_week,
    ),
    path("profile/", views.profile, name="profile"),
    path("v2/profile/", views.profile_v2, name="profile_v2"),
    path(
        "profile/<int:pk>/delete/",
        views.DeleteProfile.as_view(),
        name="delete_profile",
    ),
    path("search/", views.search, name="search"),
    path("v2/search/", views.search, name="search_v2"),
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
    # AUTH URLS
    path("login/", views.auth.login, name="login"),
    path("cognito-callback/", views.auth.cognito_callback, name="cognito_callback"),
    path("logout/", views.auth.logout, name="logout"),
]
