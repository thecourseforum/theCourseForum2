# Generated by Django 4.2.16 on 2024-11-21 17:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0016_course_title_gin_index"),
    ]

    operations = [
        migrations.CreateModel(
            name="SectionTime",
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
                ("monday", models.BooleanField(default=False)),
                ("tuesday", models.BooleanField(default=False)),
                ("wednesday", models.BooleanField(default=False)),
                ("thursday", models.BooleanField(default=False)),
                ("friday", models.BooleanField(default=False)),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                (
                    "section",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="tcf_website.section",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["monday"], name="tcf_website_monday_201753_idx"
                    ),
                    models.Index(
                        fields=["tuesday"], name="tcf_website_tuesday_a197a4_idx"
                    ),
                    models.Index(
                        fields=["wednesday"], name="tcf_website_wednesd_161943_idx"
                    ),
                    models.Index(
                        fields=["thursday"], name="tcf_website_thursda_ea277b_idx"
                    ),
                    models.Index(
                        fields=["friday"], name="tcf_website_friday_f63a33_idx"
                    ),
                    models.Index(
                        fields=["start_time"], name="tcf_website_start_t_12da2b_idx"
                    ),
                    models.Index(
                        fields=["end_time"], name="tcf_website_end_tim_63631f_idx"
                    ),
                ],
            },
        ),
    ]
