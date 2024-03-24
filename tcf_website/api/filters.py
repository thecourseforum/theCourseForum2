""""Custom DRF pagination classes"""

from django_filters import FilterSet, NumberFilter

from ..models import Instructor, Semester

# pylint: disable=unused-argument


class InstructorFilter(FilterSet):
    """Filter for Instructor"""

    course = NumberFilter(method="filter_recent_instructors_by_course")

    def filter_recent_instructors_by_course(self, queryset, name, value):
        """Filters instructors who taught the course in the recent 5 years"""
        return queryset.filter(
            section__course=value,
            section__semester__year__gte=Semester.latest().year - 5,
        ).distinct()

    class Meta:
        model = Instructor
        fields = ["course"]
