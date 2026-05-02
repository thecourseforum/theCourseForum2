import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0028_question_department_and_optional_course"),
    ]

    operations = [
        migrations.AlterField(
            model_name="answer",
            name="semester",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="tcf_website.semester",
            ),
        ),
    ]
