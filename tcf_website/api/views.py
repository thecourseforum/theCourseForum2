# pylint: disable=too-many-ancestors
"""DRF Viewsets"""
from django.db.models import Avg
from rest_framework import viewsets
from ..models import (Course, Department, Instructor, School, Semester,
                      Subdepartment)
from .paginations import FlexiblePagination
from .serializers import (CourseSerializer, CourseSimpleStatsSerializer,
                          CourseAllStatsSerializer,
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
        if 'allstats' in self.request.query_params:
            queryset = queryset\
                .prefetch_related('review_set')\
                .annotate(
                    # ratings
                    average_instructor=Avg('review__instructor_rating'),
                    average_fun=Avg('review__enjoyability'),
                    average_recommendability=Avg('review__recommendability'),
                    average_difficulty=Avg('review__difficulty'),
                    average_rating=(
                        Avg('review__instructor_rating') +
                        Avg('review__enjoyability') +
                        Avg('review__recommendability')
                    ) / 3,
                    # workload
                    average_hours_per_week=Avg('review__hours_per_week'),
                    average_amount_reading=Avg('review__amount_reading'),
                    average_amount_writing=Avg('review__amount_writing'),
                    average_amount_group=Avg('review__amount_group'),
                    average_amount_homework=Avg('review__amount_homework'),
                )
        elif 'simplestats' in self.request.query_params:
            queryset = queryset\
                .prefetch_related('review_set')\
                .annotate(
                    average_difficulty=Avg('review__difficulty'),
                    average_rating=(
                        Avg('review__instructor_rating') +
                        Avg('review__enjoyability') +
                        Avg('review__recommendability')
                    ) / 3)
        if 'recent5years' in self.request.query_params:
            latest_semester = Semester.latest()
            queryset = queryset.filter(
                semester_last_taught__year__gte=latest_semester.year - 5
            )
        return queryset.order_by('number')

    def get_serializer_class(self):
        if 'allstats' in self.request.query_params:
            return CourseAllStatsSerializer
        if 'simplestats' in self.request.query_params:
            return CourseSimpleStatsSerializer
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
