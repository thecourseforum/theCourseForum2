import django.db.models.deletion
import django.db.models.functions.text
from django.db import migrations, models
from django.db.models import Count

from tcf_website.management.instructor_merge import merge_instructor_group

EMAIL_CORRECTIONS = {
    ("ebf2px@virginia.edu", "Elizabeth", "Barnes"): "ejb5r@virginia.edu",
}


def merge_instructors_sharing_email(apps, schema_editor):
    Instructor = apps.get_model("tcf_website", "Instructor")

    for (email, first_name, last_name), corrected in EMAIL_CORRECTIONS.items():
        Instructor.objects.filter(
            email__iexact=email, first_name=first_name, last_name=last_name
        ).update(email=corrected)

    duplicate_emails = (
        Instructor.objects.exclude(email="")
        .annotate(normalized=django.db.models.functions.text.Lower("email"))
        .values("normalized")
        .annotate(n=Count("id"))
        .filter(n__gt=1)
        .values_list("normalized", flat=True)
    )

    for email in list(duplicate_emails):
        ids = list(
            Instructor.objects.filter(email__iexact=email)
            .order_by("id")
            .values_list("id", flat=True)
        )
        merge_instructor_group(apps, ids, email)


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0029_school_of_data_science"),
    ]

    operations = [
        migrations.CreateModel(
            name="InstructorAlias",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("first_name", models.CharField(blank=True, max_length=255)),
                ("last_name", models.CharField(max_length=255)),
                (
                    "instructor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="aliases",
                        to="tcf_website.instructor",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["last_name", "first_name"],
                        name="tcf_website_last_na_b30480_idx",
                    )
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("instructor", "first_name", "last_name"),
                        name="unique_instructor_alias",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="InstructorRedirect",
            fields=[
                ("old_id", models.IntegerField(primary_key=True, serialize=False)),
                (
                    "instructor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="redirects",
                        to="tcf_website.instructor",
                    ),
                ),
            ],
        ),
        migrations.RunPython(
            merge_instructors_sharing_email, migrations.RunPython.noop
        ),
    ]
