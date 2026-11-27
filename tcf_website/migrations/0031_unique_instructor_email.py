import django.db.models.functions.text
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0030_instructor_email_identity"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="instructor",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("email"),
                condition=models.Q(("email", ""), _negated=True),
                name="unique_instructor_email",
            ),
        ),
    ]
