# pylint: disable=too-many-ancestors,fixme
"""DRF Viewsets"""
from django.db.models import Avg, Sum
from rest_framework import viewsets

from ..models import (
    Course,
    Department,
    Instructor,
    School,
    Semester,
    Subdepartment,
)
from .filters import InstructorFilter
from .paginations import FlexiblePagination
from .serializers import (
    CourseAllStatsSerializer,
    CourseSerializer,
    CourseSimpleStatsSerializer,
    DepartmentSerializer,
    InstructorSerializer,
    SchoolSerializer,
    SemesterSerializer,
    SubdepartmentSerializer,
)


class SchoolViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for School"""

    queryset = School.objects.all()
    serializer_class = SchoolSerializer


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for Department"""

    queryset = Department.objects.prefetch_related("school")
    serializer_class = DepartmentSerializer


class SubdepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for Subdepartment"""

    queryset = Subdepartment.objects.all()
    serializer_class = SubdepartmentSerializer


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for Course"""

    queryset = Course.objects.select_related(
        "subdepartment", "semester_last_taught"
    )
    pagination_class = FlexiblePagination
    filterset_fields = ["subdepartment"]

    def get_queryset(self):
        queryset = self.queryset
        if "allstats" in self.request.query_params:
            queryset = queryset.prefetch_related("review_set").annotate(
                # ratings
                average_instructor=Avg("review__instructor_rating"),
                average_fun=Avg("review__enjoyability"),
                average_recommendability=Avg("review__recommendability"),
                average_difficulty=Avg("review__difficulty"),
                average_rating=(
                    Avg("review__instructor_rating")
                    + Avg("review__enjoyability")
                    + Avg("review__recommendability")
                )
                / 3,
                # workload
                average_hours_per_week=Avg("review__hours_per_week"),
                average_amount_reading=Avg("review__amount_reading"),
                average_amount_writing=Avg("review__amount_writing"),
                average_amount_group=Avg("review__amount_group"),
                average_amount_homework=Avg("review__amount_homework"),
                # grades
                # TODO: average_gpa should be fixed
                average_gpa=Avg("coursegrade__average", distinct=True),
                a_plus=Sum("coursegrade__a_plus", distinct=True),
                a=Sum("coursegrade__a", distinct=True),
                a_minus=Sum("coursegrade__a_minus", distinct=True),
                b_plus=Sum("coursegrade__b_plus", distinct=True),
                b=Sum("coursegrade__b", distinct=True),
                b_minus=Sum("coursegrade__b_minus", distinct=True),
                c_plus=Sum("coursegrade__c_plus", distinct=True),
                c=Sum("coursegrade__c", distinct=True),
                c_minus=Sum("coursegrade__c_minus", distinct=True),
                dfw=Sum("coursegrade__dfw", distinct=True),
                total_enrolled=Sum(
                    "coursegrade__total_enrolled", distinct=True
                ),
            )
        elif "simplestats" in self.request.query_params:
            queryset = queryset.prefetch_related("review_set").annotate(
                average_gpa=Avg("coursegrade__average"),
                average_difficulty=Avg("review__difficulty"),
                average_rating=(
                    Avg("review__instructor_rating")
                    + Avg("review__enjoyability")
                    + Avg("review__recommendability")
                )
                / 3,
            )
        if "recent" in self.request.query_params:
            latest_semester = Semester.latest()
            queryset = queryset.filter(
                semester_last_taught__year__gte=latest_semester.year - 5
            )
        return queryset.order_by("number")

    def get_serializer_class(self):
        if "allstats" in self.request.query_params:
            return CourseAllStatsSerializer
        if "simplestats" in self.request.query_params:
            return CourseSimpleStatsSerializer
        return CourseSerializer


class InstructorViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for Instructor"""

    queryset = Instructor.objects.all()
    serializer_class = InstructorSerializer
    pagination_class = FlexiblePagination
    filterset_class = InstructorFilter

    def get_queryset(self):
        # Returns filtered instructors ordered by last name
        return self.queryset.order_by("last_name")


class SemesterViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for Semester"""

    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer

    def get_queryset(self):
        # TODO: Refactor using django-filter if possible
        # Can't use `.filter()` twice, so use a dict
        # https://stackoverflow.com/q/8164675/
        params = {"year__gte": Semester.latest().year - 5}
        if "course" in self.request.query_params:
            params["section__course"] = self.request.query_params["course"]
        if "instructor" in self.request.query_params:
            params["section__instructors"] = self.request.query_params[
                "instructor"
            ]
        # Returns filtered, unique semesters in reverse chronological order
        return self.queryset.filter(**params).distinct().order_by("-number")
