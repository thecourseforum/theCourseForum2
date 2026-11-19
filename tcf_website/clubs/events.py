"""Validated event filters and one reusable query for event occurrences."""

from calendar import monthrange
from datetime import date, datetime, time, timedelta

from django import forms
from django.db.models import Q
from django.utils import timezone

from tcf_website.models import Club, ClubCategory, ClubEvent
from tcf_website.models.club_event import EVENT_TIME_ZONE


def public_events():
    """Only public, hosted occurrences are browseable, including in detail views."""
    return (
        ClubEvent.objects.filter(is_public=True, hosts__isnull=False)
        .select_related("category")
        .prefetch_related("hosts__category")
        .distinct()
    )


class ClubEventFilterForm(forms.Form):
    """GET form shared by full-page and progressively enhanced list requests."""

    q = forms.CharField(
        label="Search events",
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Event, club, keyword or location"}
        ),
    )
    category = forms.ModelChoiceField(
        ClubCategory.objects.order_by("name"),
        required=False,
        empty_label="All categories",
    )
    club = forms.ModelChoiceField(
        Club.objects.order_by("name"), required=False, empty_label="All clubs"
    )
    sort = forms.ChoiceField(
        label="Sort by",
        required=False,
        choices=[("soonest", "Soonest first"), ("latest", "Latest first")],
    )
    interest = forms.ChoiceField(required=False)
    show_cancelled = forms.BooleanField(label="Show canceled events", required=False)

    def __init__(self, data=None, *args, **kwargs):
        """Bind filters with Eastern-month defaults and public-event interests.

        Preserve explicitly blank dates so callers can remove either boundary.
        Apply the existing site's control styles to the generated widgets.
        """
        today = timezone.localdate(timezone=EVENT_TIME_ZONE)
        data = data.copy() if data is not None else {}
        data.setdefault("from", today.replace(day=1).isoformat())
        data.setdefault(
            "to", today.replace(day=monthrange(today.year, today.month)[1]).isoformat()
        )
        super().__init__(data, *args, **kwargs)
        for name in ("from", "to"):
            self.fields[name] = forms.DateField(
                label=name.capitalize(),
                required=False,
                widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            )
        interests = sorted(
            {
                name
                for values in public_events()
                .order_by()
                .values_list("interests", flat=True)
                for name in values
            }
        )
        self.fields["interest"].choices = [
            ("", "All interests"),
            *[(name, name) for name in interests],
        ]
        self.order_fields(
            [
                "q",
                "category",
                "club",
                "sort",
                "from",
                "to",
                "interest",
                "show_cancelled",
            ]
        )
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "checkbox"
                if isinstance(field, forms.BooleanField)
                else "select"
                if isinstance(field.widget, forms.Select)
                else "input"
            )

    def clean(self):
        """Reject reversed ranges and end dates without a representable next day."""
        cleaned = super().clean()
        start, end = cleaned.get("from"), cleaned.get("to")
        if start and end and end < start:
            self.add_error("to", "Choose an end date on or after the start date.")
        if end == date.max:
            self.add_error("to", "Choose an end date before December 31, 9999.")
        return cleaned


def filtered_events(form):
    """Intersect filter types and deduplicate co-hosts; dates include overlaps."""
    events = public_events()
    if not form.is_valid():
        return events.none()
    filters = form.cleaned_data
    if not filters["show_cancelled"]:
        events = events.filter(is_cancelled=False)
    if keyword := filters["q"]:
        events = events.filter(
            Q(title__icontains=keyword)
            | Q(description__icontains=keyword)
            | Q(hosts__name__icontains=keyword)
            | Q(location__icontains=keyword)
        )
    if category := filters["category"]:
        events = events.filter(category=category)
    if club := filters["club"]:
        events = events.filter(hosts=club)
    if interest := filters["interest"]:
        events = events.filter(interests__contains=[interest])
    if start := filters["from"]:
        events = events.filter(
            ends_at__gt=datetime.combine(start, time.min, EVENT_TIME_ZONE)
        )
    if end := filters["to"]:
        # Construct the next local midnight: DST days need not be 24 hours long.
        events = events.filter(
            starts_at__lt=datetime.combine(
                end + timedelta(days=1), time.min, EVENT_TIME_ZONE
            )
        )
    order = "-starts_at" if filters["sort"] == "latest" else "starts_at"
    return events.order_by(order, "pk").distinct()
