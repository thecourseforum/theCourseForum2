""""Custom DRF pagination classes"""
from django_filters import FilterSet, BooleanFilter, NumberFilter
from ..models import Instructor, Semester

# pylint: disable=unused-argument,no-self-use


class InstructorFilter(FilterSet):
    """Filter for Instructor"""
    section__course = NumberFilter(field_name='section__course', distinct=True)
    recent = BooleanFilter(method='filter_recent', distinct=True)

    def filter_recent(self, queryset, name, value):
        """Filter method for most recent 5 years"""
        if value is True:
            return queryset.filter(
                section__semester__year__gt=Semester.latest().year - 5,
            )
        return queryset

    class Meta:
        model = Instructor
        fields = ['section__course', 'recent']
