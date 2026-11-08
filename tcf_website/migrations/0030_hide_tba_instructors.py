from django.db import migrations


def hide_tba_instructors(apps, schema_editor):
    alias = schema_editor.connection.alias
    Instructor = apps.get_model("tcf_website", "Instructor")
    # load_semester used to split "To Be Announced" into first "To", last
    # "Announced" and attach that row to every unassigned section.
    Instructor.objects.using(alias).filter(
        first_name__iexact="To", last_name__iexact="Announced"
    ).update(hidden=True)


class Migration(migrations.Migration):
    dependencies = [
        ("tcf_website", "0029_school_of_data_science"),
    ]

    # Leave the placeholder hidden on rollback; its prior state is unknown.
    operations = [
        migrations.RunPython(hide_tba_instructors, migrations.RunPython.noop),
    ]
