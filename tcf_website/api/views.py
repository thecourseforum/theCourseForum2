# pylint: disable=too-many-ancestors
"""DRF Viewsets"""
from rest_framework import viewsets
from ..models import Department, School
from .serializers import DepartmentSerializer, SchoolSerializer


class SchoolViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for School"""
    queryset = School.objects.all()
    serializer_class = SchoolSerializer


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for Department"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
