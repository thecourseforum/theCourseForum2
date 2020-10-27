"""Routes URLs to views"""

from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about', views.AboutView.as_view(), name='about'),
    path(
        'about/history',
        views.AboutHistoryView.as_view(),
        name='about_history'),
    path(
        'about/contributors',
        views.AboutContributorsView.as_view(),
        name='about_contributors'),
    path('privacy', views.privacy, name='privacy'),
    path('terms', views.terms, name='terms'),
    path('browse', views.browse, name='browse'),
    path('department/<int:dept_id>', views.department, name='department'),
    path('course/<int:course_id>', views.course_view, name='course'),
    path('course/<int:course_id>/<int:instructor_id>',
         views.course_instructor, name='course_instructor'),
    path(
        'instructor/<int:instructor_id>',
        views.instructor_view,
        name='instructor'),
    path('reviews/new', views.new_review, name='new_review'),
    path('reviews', views.reviews, name='reviews'),
    path('reviews/<int:review_id>/upvote', views.upvote),
    path('reviews/<int:review_id>/downvote', views.downvote),
    path('profile', views.profile, name='profile'),
    path('search', views.search, name='search'),


    # AUTH URLS
    path('accounts/profile/', views.browse),
    path('login', views.login, name='login'),
    path('login/error', views.login_error),
    path('login/collect_extra_info', views.collect_extra_info),
    path('accounts/login/', views.login),
    path('logout/', views.logout, name='logout'),
]
