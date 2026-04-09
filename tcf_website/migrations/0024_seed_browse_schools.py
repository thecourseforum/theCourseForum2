# Generated for local dev: seed School records so course browse page loads without full DB dump

from django.db import migrations


def seed_schools(apps, schema_editor):
    School = apps.get_model("tcf_website", "School")
    for name in (
        "College of Arts & Sciences",
        "School of Engineering & Applied Science",
    ):
        School.objects.get_or_create(name=name, defaults={"description": "", "website": ""})


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0023_remove_sectionenrollment_section_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_schools, noop),
    ]
