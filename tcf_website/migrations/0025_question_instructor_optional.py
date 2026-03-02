# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0024_forumcategory_forumpost_forumresponse_question_title_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="question",
            name="instructor",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="tcf_website.instructor",
            ),
        ),
    ]
