from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
<<<<<<< HEAD
    path('browse', views.browse, name='browse'),
    path('department/<int:dept_id>', views.department, name='department'),
=======
    path('about', views.about, name='about'),
    path('browse', views.browse, name='browse'),
    path('department/<int:dept_id>', views.department, name='department'),
    path('course/<int:course_id>', views.course, name='course'),
    path('course/<int:course_id>/<int:instructor_id>', views.course_instructor, name='course_instructor'),
    path('reviews/new', views.new_review, name='new_review'),
    path('reviews', views.reviews, name='reviews'),
    path('profile', views.profile, name='profile'),


    # AUTH URLS
>>>>>>> migration
    path('accounts/profile/', views.browse),
    path('login', views.login, name='login'),
    path('login/error', views.login_error),
    path('login/collect_extra_info', views.collect_extra_info),
    path('accounts/login/', views.login),
    path('logout/', views.logout, name='logout'),
]