# Generated by Django 4.2.13 on 2024-11-04 01:28

import django.contrib.postgres.indexes
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0015_remove_course_tcf_website_subdepa_f296bc_idx_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="course",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["title"], name="title_gin_index", opclasses=["gin_trgm_ops"]
            ),
        ),
    ]