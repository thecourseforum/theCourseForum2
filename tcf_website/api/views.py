# pylint: disable=too-many-ancestors
"""DRF Viewsets"""
from rest_framework import viewsets
from ..models import School
from .serializers import SchoolSerializer


class SchoolViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for School"""
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
