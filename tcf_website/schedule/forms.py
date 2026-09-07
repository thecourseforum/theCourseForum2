"""Django forms for schedule builder."""

from django import forms

from ..models import Schedule


class ScheduleForm(forms.ModelForm):
    """Django form for interacting with a schedule."""

    name = forms.CharField(max_length=100)

    class Meta:
        model = Schedule
        fields = ["name"]
