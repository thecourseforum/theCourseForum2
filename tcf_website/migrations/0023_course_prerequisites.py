# Generated manually for prerequisites field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0022_coursegrade_tcf_website_course__76e103_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="prerequisites",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
