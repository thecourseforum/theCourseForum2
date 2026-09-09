from django.db import migrations


def add_school_of_data_science(apps, schema_editor):
    alias = schema_editor.connection.alias
    School = apps.get_model("tcf_website", "School")
    Department = apps.get_model("tcf_website", "Department")
    Subdepartment = apps.get_model("tcf_website", "Subdepartment")

    school, _ = School.objects.using(alias).get_or_create(name="School of Data Science")
    department, _ = Department.objects.using(alias).get_or_create(
        name="Data Science", school=school
    )
    # DS is the school's subject in UVA's catalog. Preserve its primary key so
    # existing courses, grades, and reviews keep their relationships.
    subject, _ = Subdepartment.objects.using(alias).get_or_create(
        mnemonic="DS", defaults={"name": "Data Science", "department": department}
    )
    subject.department = department
    fields = ["department"]
    if not subject.name:
        subject.name = "Data Science"
        fields.append("name")
    subject.save(using=alias, update_fields=fields)


class Migration(migrations.Migration):
    dependencies = [
        ("tcf_website", "0028_schedule_share_token_schedulebookmark_and_more"),
    ]

    # Retain repaired catalog data on rollback: deleting it would cascade to
    # courses and reviews, and the subject's original parent is unknown.
    operations = [
        migrations.RunPython(add_school_of_data_science, migrations.RunPython.noop),
    ]
