# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0027_remove_answer_unique_answer_per_user_and_question_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="department",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="tcf_website.department",
            ),
        ),
        migrations.AlterField(
            model_name="question",
            name="course",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="tcf_website.course",
            ),
        ),
    ]
