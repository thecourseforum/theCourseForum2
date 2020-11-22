""""Custom DRF pagination classes"""
from django_filters import FilterSet, BooleanFilter, NumberFilter
from ..models import Instructor, Semester


class InstructorFilter(FilterSet):
    """Filter for Instructor"""
    section__course = NumberFilter(field_name='section__course', distinct=True)
    recent5years = BooleanFilter(method='filter_recent5years', distinct=True)

    def filter_recent5years(self, queryset, name, value):
        if value is True:
            return queryset.filter(
                section__semester__year__gt=Semester.latest().year - 5,
            )
        return queryset

    class Meta:
        model = Instructor
        fields = ['section__course', 'recent5years']
