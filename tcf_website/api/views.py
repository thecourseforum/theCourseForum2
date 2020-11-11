# pylint: disable=too-many-ancestors,fixme
"""DRF Viewsets"""
from django.db.models import Avg, Sum
from rest_framework import viewsets
from ..models import (Course, Department, Instructor, School, Semester,
                      Subdepartment)
from .paginations import FlexiblePagination
from .serializers import (CourseSerializer, CourseWithStatsSerializer,
                          DepartmentSerializer, InstructorSerializer,
                          SemesterSerializer, SchoolSerializer,
                          SubdepartmentSerializer)


class SchoolViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for School"""
    queryset = School.objects.all()
    serializer_class = SchoolSerializer


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for Department"""
    queryset = Department.objects.prefetch_related('school')
    serializer_class = DepartmentSerializer


class SubdepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for Subdepartment"""
    queryset = Subdepartment.objects.all()
    serializer_class = SubdepartmentSerializer


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for Course"""
    queryset = Course.objects\
        .select_related('subdepartment', 'semester_last_taught')
    pagination_class = FlexiblePagination
    filterset_fields = ['subdepartment']

    def get_queryset(self):
        queryset = self.queryset
        if 'stats' in self.request.query_params:
            queryset = queryset\
                .prefetch_related('review_set')\
                .annotate(average_rating=Avg('review__recommendability'))\
                .annotate(average_difficulty=Avg('review__difficulty'))\
                .annotate(
                    a_plus=Sum('coursegrade__a_plus'),
                    a=Sum('coursegrade__a'),
                    a_minus=Sum('coursegrade__a_minus'),
                    b_plus=Sum('coursegrade__b_plus'),
                    b=Sum('coursegrade__b'),
                    b_minus=Sum('coursegrade__b_minus'),
                    c_plus=Sum('coursegrade__c_plus'),
                    c=Sum('coursegrade__c'),
                    c_minus=Sum('coursegrade__c_minus'),
                    d_plus=Sum('coursegrade__d_plus'),
                    d=Sum('coursegrade__d'),
                    d_minus=Sum('coursegrade__d_minus'),
                    f=Sum('coursegrade__f'),
                    ot=Sum('coursegrade__ot'),
                    drop=Sum('coursegrade__drop'),
                    withdraw=Sum('coursegrade__withdraw'),
                )\
                .annotate(average_gpa=Avg('coursegrade__average'))
            # TODO: average_gpa should be fixed
        if 'recent5years' in self.request.query_params:
            latest_semester = Semester.latest()
            queryset = queryset.filter(
                semester_last_taught__year__gte=latest_semester.year - 5
            )
        return queryset.order_by('number')

    def get_serializer_class(self):
        if 'stats' in self.request.query_params:
            return CourseWithStatsSerializer
        return CourseSerializer


class InstructorViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for Instructor"""
    queryset = Instructor.objects.all()
    serializer_class = InstructorSerializer
    pagination_class = FlexiblePagination
    filterset_fields = ['section__course']


class SemesterViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for Semester"""
    queryset = Semester.objects.all().order_by('number')
    serializer_class = SemesterSerializer
