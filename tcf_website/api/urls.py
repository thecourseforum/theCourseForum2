"""URLs for APIs"""

from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r"schools", views.SchoolViewSet)
router.register(r"departments", views.DepartmentViewSet)
router.register(r"subdepartments", views.SubdepartmentViewSet)
router.register(r"courses", views.CourseViewSet)
router.register(r"instructors", views.InstructorViewSet)
router.register(r"semesters", views.SemesterViewSet)
router.register(r"enrollment", views.SectionEnrollmentViewSet, basename="enrollment")
router.register(r"club-categories", views.ClubCategoryViewSet)
router.register(r"clubs", views.ClubViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
