from django.db import migrations


def hide_tba_instructors(apps, schema_editor):
    alias = schema_editor.connection.alias
    Instructor = apps.get_model("tcf_website", "Instructor")
    SectionInstructor = apps.get_model("tcf_website", "Section").instructors.through
    # load_semester used to split "To Be Announced" into first "To", last
    # "Announced" and attach that row to every unassigned section.
    tba = Instructor.objects.using(alias).filter(
        first_name__iexact="To", last_name__iexact="Announced"
    )
    section_ids = list(
        SectionInstructor.objects.using(alias)
        .filter(instructor__in=tba)
        .values_list("section_id", flat=True)
    )
    # Give those sections the Staff row new loads use, so hiding the placeholder
    # does not drop them from the schedule builder. No sections, no Staff row.
    if section_ids:
        staff, _ = Instructor.objects.using(alias).get_or_create(last_name="Staff")
        SectionInstructor.objects.using(alias).bulk_create(
            [
                SectionInstructor(section_id=s, instructor_id=staff.id)
                for s in section_ids
            ],
            ignore_conflicts=True,
        )
    tba.update(hidden=True)


class Migration(migrations.Migration):
    dependencies = [
        ("tcf_website", "0029_school_of_data_science"),
    ]

    # Leave the placeholder hidden on rollback; its prior state is unknown.
    operations = [
        migrations.RunPython(hide_tba_instructors, migrations.RunPython.noop),
    ]
