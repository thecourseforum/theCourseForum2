"""Review creation form (backend validation, not HTML rendering)."""

from django import forms
from django.core.exceptions import ValidationError

from ..models import Review, Section


class ReviewForm(forms.ModelForm):
    """Form for review creation in the backend, not for rendering HTML."""

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
            "amount_reading",
            "amount_writing",
            "amount_group",
            "amount_homework",
        ]

    def clean(self):
        """Validate that either club or (course and instructor) are provided."""
        cleaned_data = super().clean()
        club = cleaned_data.get("club")
        course = cleaned_data.get("course")
        instructor = cleaned_data.get("instructor")
        semester = cleaned_data.get("semester")

        if club:
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

    def save(self, commit=True):
        """Compute `hours_per_week` before actually saving"""
        instance = super().save(commit=False)
        instance.hours_per_week = (
            instance.amount_reading
            + instance.amount_writing
            + instance.amount_group
            + instance.amount_homework
        )
        if commit:
            instance.save()
        return instance
