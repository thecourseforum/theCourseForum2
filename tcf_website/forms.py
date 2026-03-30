"""Forms for the TCF website."""

from django import forms

from .models import Discipline, School, Semester, Subdepartment


class AdvancedSearchForm(forms.Form):
    """Advanced course search form for the browse page."""

    # Basic fields
    semester = forms.ChoiceField(required=False, label="Term")
    school = forms.ChoiceField(required=False, label="School")
    subject = forms.ChoiceField(required=False, label="Subject")
    course_number = forms.CharField(required=False, label="Course Number")
    title = forms.CharField(required=False, label="Title")
    min_gpa = forms.FloatField(
        required=False, label="Min GPA", min_value=0, max_value=4
    )
    open_sections = forms.BooleanField(required=False, label="Open sections only")

    # Advanced fields
    discipline = forms.MultipleChoiceField(required=False, label="Discipline")
    level = forms.ChoiceField(required=False, label="Level")
    component = forms.CharField(required=False, label="Component")
    instructor = forms.CharField(required=False, label="Instructor")
    units_min = forms.CharField(required=False, label="Units (min)")
    units_max = forms.CharField(required=False, label="Units (max)")
    days = forms.MultipleChoiceField(
        required=False,
        label="Days of Week",
        choices=[
            ("MON", "Mon"),
            ("TUE", "Tue"),
            ("WED", "Wed"),
            ("THU", "Thu"),
            ("FRI", "Fri"),
        ],
        widget=forms.CheckboxSelectMultiple,
    )
    start_time = forms.TimeField(required=False, label="Start time")
    end_time = forms.TimeField(required=False, label="End time")
    description = forms.CharField(required=False, label="Description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        latest = Semester.latest()
        semesters = Semester.objects.filter(number__gte=latest.number - 50).order_by(
            "-number"
        )
        self.fields["semester"].choices = [("", "Any")] + [
            (s.pk, str(s)) for s in semesters
        ]

        self.fields["school"].choices = [("", "Any")] + [
            (s.pk, s.name) for s in School.objects.order_by("name")
        ]

        self.fields["subject"].choices = [("", "Any")] + [
            (sd.mnemonic, f"{sd.mnemonic} - {sd.name}")
            for sd in Subdepartment.objects.order_by("mnemonic")
        ]

        self.fields["discipline"].choices = [
            (d.name, d.name) for d in Discipline.objects.order_by("name")
        ]

        self.fields["level"].choices = [
            ("", "Any"),
            ("1", "1xxx"),
            ("2", "2xxx"),
            ("3", "3xxx"),
            ("4", "4xxx"),
            ("5", "5xxx+"),
        ]

    def has_search_params(self):
        """Return True if any search field has a value."""
        if not self.is_valid():
            return False
        return any(
            v for k, v in self.cleaned_data.items() if v and v != [] and k != "page"
        )
