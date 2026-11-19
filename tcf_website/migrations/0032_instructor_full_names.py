import csv

from django.db import migrations, models
from django.db.models import Count, Max, Q
from django.db.models.functions import Lower

from tcf_website.management.instructor_merge import merge_instructor_into
from tcf_website.management.instructor_names import (
    SEMESTER_CSV_DIR,
    load_grade_last_names,
    semester_number,
    split_instructor_name,
)

INSTRUCTOR_COLUMNS = ("Instructor1", "Instructor2", "Instructor3", "Instructor4")
PLACEHOLDER_NAMES = {"Staff", "Faculty Staff", "Faculty", "To Be Announced", "-"}


def backfill_full_names(apps, schema_editor):
    Instructor = apps.get_model("tcf_website", "Instructor")
    Section = apps.get_model("tcf_website", "Section")
    SectionInstructor = Section.instructors.through

    if not SEMESTER_CSV_DIR.is_dir():
        return

    teaching = {}
    for row in SectionInstructor.objects.values_list(
        "section__semester__number",
        "section__sis_section_number",
        "instructor_id",
        "instructor__first_name",
        "instructor__last_name",
    ).iterator(chunk_size=10000):
        number, class_number, instructor_id, first_name, last_name = row
        teaching.setdefault((number, class_number), []).append(
            (instructor_id, first_name, last_name)
        )

    files = sorted(
        (
            (number, path)
            for path in SEMESTER_CSV_DIR.glob("*.csv")
            if (number := semester_number(path)) is not None
        ),
        reverse=True,
    )

    full_names = {}
    for number, path in files:
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            for row in csv.DictReader(handle):
                try:
                    class_number = int(float(row.get("ClassNumber") or ""))
                except ValueError:
                    continue
                instructors = teaching.get((number, class_number))
                if not instructors:
                    continue
                for column in INSTRUCTOR_COLUMNS:
                    for name in (row.get(column) or "").split(","):
                        name = " ".join(name.split())
                        if not name or name in PLACEHOLDER_NAMES:
                            continue
                        parts = name.split()
                        for instructor_id, first_name, last_name in instructors:
                            if instructor_id in full_names:
                                continue
                            if (first_name, last_name) == (parts[0], parts[-1]):
                                full_names[instructor_id] = name

    grade_last_names = load_grade_last_names()
    changed = []
    for instructor in Instructor.objects.only(
        "id", "first_name", "last_name", "full_name"
    ).iterator(chunk_size=2000):
        full_name = full_names.get(instructor.id, instructor.full_name)
        if len(full_name.split()) < 2:
            continue
        first_name, last_name = split_instructor_name(full_name, grade_last_names)
        current = (instructor.first_name, instructor.last_name, instructor.full_name)
        if current != (first_name, last_name, full_name):
            instructor.first_name = first_name
            instructor.last_name = last_name
            instructor.full_name = full_name
            changed.append(instructor)
    Instructor.objects.bulk_update(
        changed, ["first_name", "last_name", "full_name"], batch_size=1000
    )

    duplicate_names = (
        Instructor.objects.exclude(full_name="")
        .annotate(normalized=Lower("full_name"))
        .values("normalized")
        .annotate(
            n=Count("id"),
            emails=Count("email", distinct=True, filter=~Q(email="")),
        )
        .filter(n__gt=1, emails__lte=1)
        .values_list("normalized", flat=True)
    )
    for normalized in list(duplicate_names):
        rows = list(
            Instructor.objects.filter(full_name__iexact=normalized)
            .annotate(latest=Max("section__semester__number"))
            .order_by("id")
        )
        newest = max(rows, key=lambda row: (row.latest or 0, row.id))
        keep = next((row for row in rows if row.email), rows[0])
        for other in rows:
            if other.pk != keep.pk:
                merge_instructor_into(apps, keep, other)
        keep.first_name = newest.first_name
        keep.last_name = newest.last_name
        keep.full_name = newest.full_name
        keep.save()


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0031_unique_instructor_email"),
    ]

    operations = [
        migrations.AlterField(
            model_name="instructor",
            name="full_name",
            field=models.CharField(blank=True, max_length=511),
        ),
        migrations.RunPython(backfill_full_names, migrations.RunPython.noop),
    ]
