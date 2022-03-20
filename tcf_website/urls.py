"""Routes URLs to views"""

from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('ads.txt/', views.ads, name='ads'),
    path('browse/', views.browse, name='browse'),
    path('department/<int:dept_id>/', views.department, name='department'),
    path('course/<int:course_id>/', views.course_view_legacy, name='course_legacy'),
    path('course/<int:course_id>/<int:instructor_id>/',
         views.course_instructor, name='course_instructor'),
    path('course/<str:mnemonic>/<int:course_number>/',
         views.course_view, name='course'),
    path('instructor/<int:instructor_id>/',
         views.instructor_view, name='instructor'),
    path('reviews/new/', views.new_review, name='new_review'),
    path('reviews/<int:pk>/delete/',
         views.DeleteReview.as_view(), name='delete_review'),
    path('reviews/<int:review_id>/edit/',
         views.edit_review, name='edit_review'),
    path('reviews/', views.reviews, name='reviews'),
    path('reviews/<int:review_id>/upvote/', views.upvote),
    path('reviews/<int:review_id>/downvote/', views.downvote),
    path('reviews/check_duplicate/', views.review.check_duplicate),
    path('reviews/check_zero_hours_per_week/', views.review.check_zero_hours_per_week),
    path('profile/', views.profile, name='profile'),
    path('search/', views.search, name='search'),

    # API URLs
    path('api/', include('tcf_website.api.urls'), name='api'),

    # FEEDBACK URLS
    path('feedback/discord', views.discord_feedback, name='discord'),
    path('feedback/email', views.email_feedback, name='email'),

    # AUTH URLS
    path('login/', views.login, name='login'),
    path('login/error/', views.login_error),
    path('login/collect_extra_info/', views.collect_extra_info),
    path('accounts/login/', views.login),
    path('logout/', views.logout, name='logout'),
]
