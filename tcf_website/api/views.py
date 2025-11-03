# pylint: disable=too-many-ancestors,fixme
"""DRF Viewsets"""
import asyncio
# from threading import Thread
from django.db import connection
from django.db.models import Avg, Sum
from django.http import JsonResponse
from rest_framework import viewsets
import requests
from ..models import (
    Club,
    ClubCategory,
    Course,
    Department,
    Instructor,
    School,
    Section,
    SectionEnrollment,
    Semester,
    Subdepartment,
)
from .filters import InstructorFilter
from .serializers import (
    ClubCategorySerializer,
    ClubSerializer,
    CourseAllStatsSerializer,
    CourseSerializer,
    CourseSimpleStatsSerializer,
    DepartmentSerializer,
    InstructorSerializer,
    SchoolSerializer,
    SemesterSerializer,
    SubdepartmentSerializer,
)
from .enrollment import update_enrollment_data


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

    queryset = Course.objects.select_related("subdepartment", "semester_last_taught")
    filterset_fields = ["subdepartment"]

    def get_queryset(self):
        queryset = super().get_queryset()

        if "recent" in self.request.query_params:
            latest_semester = Semester.latest()
            queryset = queryset.filter(
                semester_last_taught__year__gte=latest_semester.year - 5
            )

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
                average_gpa=Avg("coursegrade__average"),
                a_plus=Sum("coursegrade__a_plus"),
                a=Sum("coursegrade__a"),
                a_minus=Sum("coursegrade__a_minus"),
                b_plus=Sum("coursegrade__b_plus"),
                b=Sum("coursegrade__b"),
                b_minus=Sum("coursegrade__b_minus"),
                c_plus=Sum("coursegrade__c_plus"),
                c=Sum("coursegrade__c"),
                c_minus=Sum("coursegrade__c_minus"),
                dfw=Sum("coursegrade__dfw"),
                total_enrolled=Sum("coursegrade__total_enrolled"),
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
            params["section__instructors"] = self.request.query_params["instructor"]
        # Returns filtered, unique semesters in reverse chronological order
        return super().get_queryset().filter(**params).distinct().order_by("-number")


class ClubCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for ClubCategory"""

    queryset = ClubCategory.objects.all()
    serializer_class = ClubCategorySerializer


class ClubViewSet(viewsets.ReadOnlyModelViewSet):
    """DRF ViewSet for Club"""

    queryset = Club.objects.select_related("category")
    serializer_class = ClubSerializer
    filterset_fields = ["category"]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by category if provided in query params
        category_id = self.request.query_params.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        return queryset.order_by("name")


class SectionEnrollmentViewSet(viewsets.ViewSet):
    """ViewSet for retrieving section enrollment data."""

    def retrieve(self, request, pk=None):
        """Retrieves enrollment data for all sections of a given course."""

        # Start the update in a background thread
        def _run_update():
            try:
                asyncio.run(update_enrollment_data(pk))
            except (asyncio.TimeoutError, requests.RequestException, ValueError) as exc:
                print(f"Enrollment update failed for course {pk}: {exc}")
            finally:
                connection.close()

        # thread = Thread(target=_run_update, daemon=True)
        # thread.start()

        # Get sections and return enrollment data
        sections = Section.objects.filter(course_id=pk)
        enrollment_data = {}

        for section in sections:
            section_enrollment = SectionEnrollment.objects.filter(
                section=section
            ).first()
            if section_enrollment:
                enrollment_data[section.sis_section_number] = {
                    "enrollment_taken": section_enrollment.enrollment_taken,
                    "enrollment_limit": section_enrollment.enrollment_limit,
                    "waitlist_taken": section_enrollment.waitlist_taken,
                    "waitlist_limit": section_enrollment.waitlist_limit,
                }

        return JsonResponse({"enrollment_data": enrollment_data})
