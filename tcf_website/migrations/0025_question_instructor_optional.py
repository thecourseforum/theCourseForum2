# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0024_question_title"),
    ]

    operations = [
        migrations.AlterField(
            model_name="question",
            name="instructor",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="tcf_website.instructor",
            ),
        ),
    ]
