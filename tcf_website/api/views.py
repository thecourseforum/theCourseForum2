# pylint: disable=too-many-ancestors
"""DRF Viewsets"""
from rest_framework import viewsets
from ..models import Course, Department, Instructor, School, Subdepartment
from .paginations import MyPagination
from .serializers import (CourseSerializer, DepartmentSerializer,
                          InstructorSerializer, SchoolSerializer,
                          SubdepartmentSerializer)


class SchoolViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for School"""
    queryset = School.objects.all()
    serializer_class = SchoolSerializer


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for Department"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class SubdepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for Subdepartment"""
    queryset = Subdepartment.objects.all()
    serializer_class = SubdepartmentSerializer


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for Course"""
    queryset = Course.objects.all().order_by('number')
    serializer_class = CourseSerializer
    pagination_class = MyPagination
    filterset_fields = ['subdepartment']


class InstructorViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for Instructor"""
    queryset = Instructor.objects.all()
    serializer_class = InstructorSerializer
    pagination_class = MyPagination
    filterset_fields = ['section__course']
