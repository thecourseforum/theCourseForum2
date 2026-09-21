"""Review creation form (backend validation, not HTML rendering)."""

from django import forms
from django.core.exceptions import ValidationError

from ..models import Review, Section


class ReviewForm(forms.ModelForm):
    """Form for review creation in the backend, not for rendering HTML."""

    # Optional for courses (a ratings-only review is valid). When present it
    # must still meet the written-review bar. Clubs require it; see clean().
    text = forms.CharField(min_length=200, max_length=5000, required=False)
    # Optional on its own: clean() requires either this or the full breakdown.
    hours_per_week = forms.IntegerField(min_value=0, max_value=80, required=False)

    BREAKDOWN_FIELDS = (
        "amount_reading",
        "amount_writing",
        "amount_group",
        "amount_homework",
    )

    class Meta:
        model = Review
        fields = [
            "text",
            "course",
            "club",
            "instructor",
            "semester",
            "instructor_rating",
            "difficulty",
            "recommendability",
            "enjoyability",
            "hours_per_week",
            "amount_reading",
            "amount_writing",
            "amount_group",
            "amount_homework",
        ]

    def _clean_hours(self, cleaned_data):
        """Settle `hours_per_week`: the breakdown's sum, or the total given."""
        breakdown = [cleaned_data.get(name) for name in self.BREAKDOWN_FIELDS]
        provided = [value for value in breakdown if value is not None]
        if len(provided) == len(breakdown):
            cleaned_data["hours_per_week"] = sum(breakdown)
        elif provided:
            raise ValidationError(
                "Fill in all four weekly-hours fields or none of them."
            )
        elif cleaned_data.get("hours_per_week") is None:
            raise ValidationError("Weekly hours are required.")

    def clean(self):
        """Validate hours, then that either club or (course and instructor) are provided."""
        cleaned_data = super().clean()
        club = cleaned_data.get("club")
        course = cleaned_data.get("course")
        instructor = cleaned_data.get("instructor")
        semester = cleaned_data.get("semester")

        self._clean_hours(cleaned_data)

        # A course/club can only be reviewed for a term that has actually
        # started — never a future semester loaded for course registration.
        if semester and not semester.has_started():
            raise ValidationError(
                "You can only review a semester that has already started."
            )

        if club:
            if not cleaned_data.get("text"):
                raise ValidationError("Club reviews need a written review.")
            return cleaned_data

        if not course:
            raise ValidationError("Course is required for course reviews")
        if not instructor:
            raise ValidationError("Instructor is required for course reviews")
        if not semester:
            raise ValidationError("Semester is required for course reviews")

        if not Section.objects.filter(
            course=course, semester=semester, instructors=instructor
        ).exists():
            raise ValidationError(
                "Selected instructor did not teach this course in the chosen semester."
            )

        return cleaned_data
