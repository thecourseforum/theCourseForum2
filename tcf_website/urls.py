from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('browse', views.browse, name='browse'),
    path('department/<int:dept_id>', views.department, name='department'),
    path('accounts/profile/', views.browse),
    path('login', views.login, name='login'),
    path('login/error', views.login_error),
    path('login/collect_extra_info', views.collect_extra_info),
    path('accounts/login/', views.login),
    path('logout/', views.logout, name='logout'),
]