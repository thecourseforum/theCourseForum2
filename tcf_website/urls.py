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
        "club/<str:category_slug>/<int:club_id>/",
        views.club_view,
        name="club",
    ),
    path("", views.index, name="index"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("privacy/", views.privacy, name="privacy"),
    path("terms/", views.terms, name="terms"),
    path("browse/", views.browse, name="browse"),
    path("department/<int:dept_id>/", views.department, name="department"),
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
        "course/<int:course_id>/add-to-schedule/",
        views.schedule_add_course,
        name="schedule_add_course",
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
    path("reviews/", views.reviews, name="reviews"),
    path("reviews/<int:review_id>/upvote/", views.upvote),
    path("reviews/<int:review_id>/downvote/", views.downvote),
    path("reviews/<int:review_id>/vote/", views.vote_review, name="vote_review"),
    path(
        "reviews/check_duplicate/",
        views.review.check_duplicate,
        name="check_review_duplicate",
    ),
    path(
        "reviews/check_zero_hours_per_week/",
        views.review.check_zero_hours_per_week,
        name="check_zero_hours_per_week",
    ),
    path(
        "reviews/semesters-for-course/",
        views.review.review_semester_options,
        name="review_semester_options",
    ),
    path(
        "reviews/instructors-for-course/",
        views.review.review_instructor_options,
        name="review_instructor_options",
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
        "schedule/course/<int:scheduled_course_id>/remove/",
        views.remove_scheduled_course,
        name="remove_scheduled_course",
    ),
    path(
        "schedule/duplicate/<int:schedule_id>/",
        views.duplicate_schedule,
        name="duplicate_schedule",
    ),
    path(
        "schedule/share/",
        views.schedule_share,
        name="schedule_share",
    ),
    path(
        "schedule/unbookmark/",
        views.schedule_unbookmark,
        name="schedule_unbookmark",
    ),
    # AUTH URLs
    path("login/", views.auth.login, name="login"),
    path("cognito-callback/", views.auth.cognito_callback, name="cognito_callback"),
    path("logout/", views.auth.logout, name="logout"),
    path("forgot-password/", views.auth.forgot_password, name="forgot_password"),
]
