import csv
import json

from django.db import migrations

from tcf_website.management.instructor_merge import merge_instructor_group
from tcf_website.management.instructor_names import SEMESTER_CSV_DIR, semester_number


def name_key(name):
    parts = name.lower().split()
    return (parts[0], parts[-1]) if parts else None


def load_csv_emails():
    sections = {}
    if not SEMESTER_CSV_DIR.is_dir():
        return sections
    for path in SEMESTER_CSV_DIR.glob("*.csv"):
        number = semester_number(path)
        if number is None:
            continue
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            reader = csv.DictReader(handle)
            if "InstructorEmails" not in (reader.fieldnames or ()):
                continue
            for row in reader:
                raw = (row.get("InstructorEmails") or "").strip()
                if not raw:
                    continue
                try:
                    class_number = int(float(row.get("ClassNumber") or ""))
                except ValueError:
                    continue
                sections[(number, class_number)] = {
                    " ".join(name.split()).lower(): email.strip().lower()
                    for name, email in json.loads(raw).items()
                    if email.strip()
                }
    return sections


def collect_sis_emails(apps):
    Section = apps.get_model("tcf_website", "Section")
    csv_emails = load_csv_emails()
    numbers = {number for number, _ in csv_emails}
    found = {}
    for row in (
        Section.instructors.through.objects.filter(
            section__semester__number__in=numbers
        )
        .values_list(
            "section__semester__number",
            "section__sis_section_number",
            "instructor_id",
            "instructor__full_name",
            "instructor__first_name",
            "instructor__last_name",
        )
        .iterator(chunk_size=10000)
    ):
        number, class_number, instructor_id, full_name, first_name, last_name = row
        emails = csv_emails.get((number, class_number))
        if not emails:
            continue
        full_name = " ".join((full_name or f"{first_name} {last_name}").split()).lower()
        email = emails.get(full_name)
        if email is None:
            key = name_key(full_name)
            matches = {value for name, value in emails.items() if name_key(name) == key}
            email = matches.pop() if len(matches) == 1 else None
        if email:
            found.setdefault(instructor_id, set()).add(email)
    return found


def backfill_sis_emails(apps, schema_editor):
    Instructor = apps.get_model("tcf_website", "Instructor")
    for instructor_id, emails in sorted(collect_sis_emails(apps).items()):
        if len(emails) != 1:
            continue
        email = next(iter(emails))
        instructor = Instructor.objects.filter(id=instructor_id).first()
        if instructor is None or instructor.email:
            continue
        existing = (
            Instructor.objects.filter(email__iexact=email)
            .exclude(id=instructor_id)
            .first()
        )
        if existing:
            merge_instructor_group(apps, [existing.id, instructor_id], email)
        else:
            instructor.email = email
            instructor.save(update_fields=["email"])


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0032_instructor_full_names"),
    ]

    operations = [
        migrations.RunPython(backfill_sis_emails, migrations.RunPython.noop),
    ]
