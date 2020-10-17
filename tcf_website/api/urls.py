"""URLs for APIs"""
from django.urls import include, path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'schools', views.SchoolViewSet)
router.register(r'departments', views.DepartmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
