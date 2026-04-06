"""Forms for the TCF website."""

from django import forms

from .models import ClubCategory, Discipline, School, Semester, Subdepartment
from .utils import recent_semesters


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
    sort = forms.ChoiceField(
        required=False,
        label="Sort by",
        choices=[
            ("", "Course # (A–Z)"),
            ("rating_desc", "Rating (High–Low)"),
            ("gpa_desc", "GPA (High–Low)"),
            ("difficulty_asc", "Difficulty (Low–High)"),
        ],
    )

    # Advanced fields
    discipline = forms.MultipleChoiceField(required=False, label="Discipline")
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
        semesters = recent_semesters()
        self.fields["semester"].choices = [("", "Any")] + [
            (s.pk, str(s)) for s in semesters
        ]
        if latest is not None:
            self.fields["semester"].initial = latest.pk

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

    _ADVANCED_FIELDS = frozenset(
        (
            "component",
            "instructor",
            "sort",
            "units_min",
            "units_max",
            "days",
            "start_time",
            "end_time",
            "description",
            "open_sections",
            "discipline",
        )
    )

    def has_search_params(self):
        """Return True if any search field has a value."""
        if not self.is_valid():
            return False
        return any(
            v
            for k, v in self.cleaned_data.items()
            if v and v != [] and k not in ("page", "sort")
        )

    def has_advanced_params(self):
        """Return True if any advanced (hidden) field has a value."""
        if not self.is_valid():
            return False
        return any(self.cleaned_data.get(f) for f in self._ADVANCED_FIELDS)


class ClubAdvancedSearchForm(forms.Form):
    """Club browse filters (category, name, application required)."""

    category = forms.ChoiceField(required=False, label="Category")
    club_name = forms.CharField(required=False, label="Club name")
    no_application_required = forms.BooleanField(
        required=False, label="No application required"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].choices = [("", "Any")] + [
            (str(c.pk), c.name) for c in ClubCategory.objects.order_by("name")
        ]

    def has_search_params(self):
        """Return True if any filter is active."""
        if not self.is_valid():
            return False
        data = self.cleaned_data
        if data.get("category"):
            return True
        if (data.get("club_name") or "").strip():
            return True
        if data.get("no_application_required"):
            return True
        return False
