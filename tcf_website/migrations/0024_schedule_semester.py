# Existing Schedule rows get semester_id=1; change default=1 if that pk is missing.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0023_remove_sectionenrollment_section_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="schedule",
            name="semester",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="tcf_website.semester",
            ),
            preserve_default=False,
        ),
        migrations.AddIndex(
            model_name="schedule",
            index=models.Index(
                fields=["user", "semester"],
                name="tcf_website_user_id_3b30ed_idx",
            ),
        ),
    ]
