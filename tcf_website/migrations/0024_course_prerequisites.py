# Generated manually for prerequisites field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0023_remove_sectionenrollment_section_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="prerequisites",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
