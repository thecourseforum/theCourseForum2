""""Custom DRF pagination classes"""
from django_filters import FilterSet, NumberFilter
from ..models import Instructor


class InstructorFilter(FilterSet):
    """Filter for Instructor"""
    section__course = NumberFilter(field_name='section__course', distinct=True)

    class Meta:
        model = Instructor
        fields = ['section__course']
